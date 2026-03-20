from celery import shared_task
from html import escape
from django.db import transaction
from django.db.models import F
from django.db.models import Max
from django.utils import timezone

from apps.ai_platform.registry import get_provider_handler
from apps.ai_platform.services.runtime_resolver import (
    RuntimeResolutionError,
    resolve_runtime,
)
from blog.models import NoteHeader, NoteTextContent

from .models import AIGenerationJob, AIGenerationLog
from .services.output_contract import apply_output_contract


def _build_context_payload(job: AIGenerationJob):
    note = job.note
    headers = [
        {**h, 'uuid': str(h['uuid'])}
        for h in note.headers.order_by('order').values('uuid', 'level', 'text', 'order')
    ]
    text_contents = [
        {**t, 'uuid': str(t['uuid'])}
        for t in note.text_contents.order_by('order').values('uuid', 'html', 'order')
    ]
    return {
        'note_uuid': str(note.uuid),
        'note_title': note.title,
        'note_body': note.body,
        'headers': headers,
        'text_contents': text_contents,
        'source_block_uuid': (
            str(job.source_block_uuid)
            if job.source_block_uuid
            else None
        ),
    }


def _normalize_header_level(level_value):
    if isinstance(level_value, int):
        return 3 if level_value == 3 else 2

    if isinstance(level_value, str):
        normalized = level_value.strip().lower()
        if normalized in {'h2', '2'}:
            return 2
        if normalized in {'h3', '3'}:
            return 3

    return 2


def _normalize_operations(raw_operations):
    if not isinstance(raw_operations, list):
        return []

    normalized_operations = []
    for operation in raw_operations:
        if not isinstance(operation, dict):
            continue

        operation_type = str(operation.get('type', '')).strip().lower()

        if operation_type in {
            'insert_header',
            'insert_heading',
            'header',
            'heading',
            'add_header',
            'add_heading',
            'h2',
            'h3',
        }:
            text = (
                operation.get('text')
                or operation.get('title')
                or operation.get('heading')
                or ''
            )
            if not str(text).strip():
                continue

            level = operation.get('level')
            if operation_type in {'h2', 'h3'} and level is None:
                level = operation_type

            normalized_operations.append({
                'type': 'insert_header',
                'text': str(text).strip(),
                'level': _normalize_header_level(level),
            })
            continue

        if operation_type in {
            'insert_text',
            'text',
            'paragraph',
            'insert_paragraph',
            'add_text',
        }:
            html = operation.get('html')
            if not html:
                text_value = (
                    operation.get('text')
                    or operation.get('content')
                    or ''
                )
                text_value = str(text_value).strip()
                if not text_value:
                    continue
                html = f'<p>{escape(text_value)}</p>'

            normalized_operations.append({
                'type': 'insert_text',
                'html': str(html),
            })

    return normalized_operations


def _apply_operations(job: AIGenerationJob, operations):
    note = job.note

    max_header_order = note.headers.aggregate(models_max=Max('order'))[
        'models_max'
    ]
    max_text_order = note.text_contents.aggregate(models_max=Max('order'))[
        'models_max'
    ]
    next_order = max(max_header_order or -1, max_text_order or -1) + 1

    created_headers = []
    created_texts = []
    source_order = None

    if job.source_block_uuid:
        source_header = NoteHeader.objects.filter(
            note=note,
            uuid=job.source_block_uuid,
        ).only('order').first()
        if source_header:
            source_order = source_header.order
        else:
            source_text = NoteTextContent.objects.filter(
                note=note,
                uuid=job.source_block_uuid,
            ).only('order').first()
            if not source_text:
                raise ValueError(
                    'Source block not found for AI generation job.'
                )
            source_order = source_text.order

    if source_order is not None and operations:
        shift_by = len(operations)
        NoteHeader.objects.filter(note=note, order__gt=source_order).update(
            order=F('order') + shift_by
        )
        NoteTextContent.objects.filter(
            note=note,
            order__gt=source_order,
        ).update(order=F('order') + shift_by)
        next_order = source_order + 1

    for operation in operations:
        operation_type = operation.get('type')

        if operation_type == 'insert_header':
            header = NoteHeader.objects.create(
                note=note,
                text=operation.get('text', ''),
                level=_normalize_header_level(operation.get('level', 2)),
                order=next_order,
            )
            created_headers.append(str(header.uuid))
            next_order += 1

        if operation_type == 'insert_text':
            text_content = NoteTextContent.objects.create(
                note=note,
                html=operation.get('html', ''),
                order=next_order,
            )
            created_texts.append(str(text_content.uuid))
            next_order += 1

    return {
        'created_headers': created_headers,
        'created_text_blocks': created_texts,
    }


def _duration_ms(started_at, finished_at):
    if not started_at or not finished_at:
        return None
    return max(
        int((finished_at - started_at).total_seconds() * 1000),
        0,
    )


@shared_task(
    bind=True,
    autoretry_for=(RuntimeResolutionError,),
    retry_backoff=True,
    max_retries=2,
)
def execute_generation_job(self, job_uuid: str):
    job = AIGenerationJob.objects.select_related('note').get(uuid=job_uuid)
    generation_log = None
    response = None
    operations = []

    job.status = AIGenerationJob.STATUS_RUNNING
    job.started_at = timezone.now()
    job.celery_task_id = self.request.id or ''
    job.save(
        update_fields=['status', 'started_at', 'celery_task_id', 'updated_at']
    )

    try:
        runtime = resolve_runtime(operation_type=job.operation_type)
        handler = get_provider_handler(runtime['provider'].code)
        context_payload = _build_context_payload(job)

        prompt_payload = {
            'system': apply_output_contract(
                runtime['prompt_template'].system_prompt
            ),
            'template': runtime['prompt_template'].user_prompt_template,
            'operation_type': job.operation_type,
        }
        options_payload = {
            'temperature': runtime['global_config'].default_temperature,
            'max_tokens': runtime['global_config'].default_max_tokens,
            'operation_type': job.operation_type,
        }
        request_metadata = {
            'provider': runtime['provider'].code,
            'model': runtime['model'].code,
            'base_url': (
                runtime['credential'].base_url
                if runtime['credential']
                else ''
            ),
            'organization': (
                runtime['credential'].organization
                if runtime['credential']
                else ''
            ),
        }

        generation_log = AIGenerationLog.objects.create(
            job=job,
            owner=job.owner,
            note=job.note,
            operation_type=job.operation_type,
            provider_code=runtime['provider'].code,
            model_code=runtime['model'].code,
            status=AIGenerationLog.STATUS_RUNNING,
            celery_task_id=job.celery_task_id,
            request_prompt=prompt_payload,
            request_options=options_payload,
            request_context=context_payload,
            request_metadata=request_metadata,
            started_at=job.started_at,
        )

        response = handler.generate(
            model_code=runtime['model'].code,
            prompt=prompt_payload,
            options=options_payload,
            credentials={
                'api_key': (
                    runtime['credential'].api_key
                    if runtime['credential']
                    else ''
                ),
                'base_url': (
                    runtime['credential'].base_url
                    if runtime['credential']
                    else ''
                ),
                'organization': (
                    runtime['credential'].organization
                    if runtime['credential']
                    else ''
                ),
            },
            context=context_payload,
        )

        operations = _normalize_operations(response.get('operations', []))
        if generation_log:
            generation_log.response_payload = response
            generation_log.normalized_operations = operations
            generation_log.save(
                update_fields=['response_payload', 'normalized_operations']
            )

        if not operations:
            raise ValueError(
                f'AI provider returned no applicable operations for the note. '
                f'Raw response: {response!r}'
            )

        with transaction.atomic():
            applied = _apply_operations(job, operations)
            job.status = AIGenerationJob.STATUS_SUCCEEDED
            job.finished_at = timezone.now()
            job.result_payload = {
                'provider': runtime['provider'].code,
                'model': runtime['model'].code,
                'operations': operations,
                'applied': applied,
            }
            job.save(
                update_fields=[
                    'status',
                    'finished_at',
                    'result_payload',
                    'updated_at',
                ]
            )

            if generation_log:
                generation_log.status = AIGenerationLog.STATUS_SUCCEEDED
                generation_log.result_metadata = {
                    'applied': applied,
                    'job_status': job.status,
                }
                generation_log.finished_at = job.finished_at
                generation_log.duration_ms = _duration_ms(
                    generation_log.started_at,
                    generation_log.finished_at,
                )
                generation_log.save(
                    update_fields=[
                        'status',
                        'response_payload',
                        'normalized_operations',
                        'result_metadata',
                        'finished_at',
                        'duration_ms',
                    ]
                )

    except Exception as exc:
        job.status = AIGenerationJob.STATUS_FAILED
        job.finished_at = timezone.now()
        job.error_message = str(exc)
        job.save(
            update_fields=[
                'status',
                'finished_at',
                'error_message',
                'updated_at',
            ]
        )

        if generation_log is None:
            generation_log = AIGenerationLog.objects.create(
                job=job,
                owner=job.owner,
                note=job.note,
                operation_type=job.operation_type,
                status=AIGenerationLog.STATUS_FAILED,
                celery_task_id=job.celery_task_id,
                error_message=str(exc),
                started_at=job.started_at,
                finished_at=job.finished_at,
                duration_ms=_duration_ms(job.started_at, job.finished_at),
                result_metadata={'job_status': job.status},
            )
        else:
            generation_log.status = AIGenerationLog.STATUS_FAILED
            if response is not None:
                generation_log.response_payload = response
                generation_log.normalized_operations = operations
            generation_log.error_message = str(exc)
            generation_log.finished_at = job.finished_at
            generation_log.duration_ms = _duration_ms(
                generation_log.started_at,
                generation_log.finished_at,
            )
            generation_log.save(
                update_fields=[
                    'status',
                    'response_payload',
                    'normalized_operations',
                    'error_message',
                    'finished_at',
                    'duration_ms',
                ]
            )
        raise
