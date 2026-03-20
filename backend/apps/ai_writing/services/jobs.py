from apps.ai_writing.models import AIGenerationJob
from apps.ai_writing.tasks import execute_generation_job


def create_generation_job(*, owner, note, operation_type, source_block_uuid=None, request_payload=None, idempotency_key=''):
    request_payload = request_payload or {}

    if idempotency_key:
        existing = (
            AIGenerationJob.objects
            .filter(owner=owner, note=note, idempotency_key=idempotency_key)
            .exclude(status=AIGenerationJob.STATUS_FAILED)
            .order_by('-created_at')
            .first()
        )
        if existing:
            return existing

    job = AIGenerationJob.objects.create(
        owner=owner,
        note=note,
        operation_type=operation_type,
        source_block_uuid=source_block_uuid,
        request_payload=request_payload,
        idempotency_key=idempotency_key,
    )

    execute_generation_job.delay(str(job.uuid))
    return job
