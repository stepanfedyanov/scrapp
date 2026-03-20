from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_platform.constants import (
    OPERATION_WRITE_MORE_TEXT,
    OPERATION_WRITE_NOTE,
)
from apps.ai_writing.models import AIGenerationJob, AIGenerationLog
from apps.ai_writing.services.jobs import create_generation_job
from apps.ai_writing.tasks import (
    _apply_operations,
    _normalize_operations,
    execute_generation_job,
)
from apps.ai_writing.services.output_contract import OUTPUT_FORMAT_CONTRACT
from blog.models import Blog, Note, NoteHeader, NoteTextContent

User = get_user_model()


class AIWritingServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='jobs-user',
            email='jobs@example.com',
            password='testpass123',
        )
        self.blog = Blog.objects.create(owner=self.user, title='Jobs Blog')
        self.note = Note.objects.create(
            blog=self.blog,
            title='Jobs Note',
            body='',
        )

    @patch('apps.ai_writing.services.jobs.execute_generation_job.delay')
    def test_create_generation_job_reuses_non_failed_job_by_idempotency_key(
        self,
        delay_mock,
    ):
        first_job = create_generation_job(
            owner=self.user,
            note=self.note,
            operation_type=OPERATION_WRITE_NOTE,
            idempotency_key='same-key',
        )

        second_job = create_generation_job(
            owner=self.user,
            note=self.note,
            operation_type=OPERATION_WRITE_NOTE,
            idempotency_key='same-key',
        )

        self.assertEqual(first_job.uuid, second_job.uuid)
        self.assertEqual(AIGenerationJob.objects.count(), 1)
        delay_mock.assert_called_once_with(str(first_job.uuid))

    def test_apply_operations_uses_shared_order_sequence(self):
        job = AIGenerationJob.objects.create(
            owner=self.user,
            note=self.note,
            operation_type=OPERATION_WRITE_NOTE,
        )

        _apply_operations(job, [
            {'type': 'insert_header', 'text': 'Intro', 'level': 2},
            {'type': 'insert_text', 'html': '<p>Body</p>'},
            {'type': 'insert_header', 'text': 'Wrap-up', 'level': 2},
        ])

        headers = list(
            self.note.headers.order_by('order').values_list(
                'order',
                flat=True,
            )
        )
        texts = list(
            self.note.text_contents.order_by('order').values_list(
                'order',
                flat=True,
            )
        )
        self.assertEqual(headers, [0, 2])
        self.assertEqual(texts, [1])

    def test_apply_operations_inserts_after_source_block(self):
        source_header = NoteHeader.objects.create(
            note=self.note,
            text='Existing header',
            level=2,
            order=0,
        )
        existing_text = NoteTextContent.objects.create(
            note=self.note,
            html='<p>Existing text</p>',
            order=1,
        )
        trailing_header = NoteHeader.objects.create(
            note=self.note,
            text='Trailing header',
            level=2,
            order=2,
        )
        job = AIGenerationJob.objects.create(
            owner=self.user,
            note=self.note,
            operation_type=OPERATION_WRITE_MORE_TEXT,
            source_block_uuid=source_header.uuid,
        )

        _apply_operations(job, [
            {'type': 'insert_text', 'html': '<p>Inserted text</p>'},
            {'type': 'insert_header', 'text': 'Inserted header', 'level': 2},
        ])

        existing_text.refresh_from_db()
        trailing_header.refresh_from_db()

        inserted_text = self.note.text_contents.exclude(
            uuid=existing_text.uuid
        ).get()
        inserted_header = self.note.headers.exclude(
            uuid__in=[source_header.uuid, trailing_header.uuid]
        ).get()

        self.assertEqual(inserted_text.order, 1)
        self.assertEqual(inserted_header.order, 2)
        self.assertEqual(existing_text.order, 3)
        self.assertEqual(trailing_header.order, 4)

    def test_apply_operations_normalizes_string_header_levels(self):
        job = AIGenerationJob.objects.create(
            owner=self.user,
            note=self.note,
            operation_type=OPERATION_WRITE_NOTE,
        )

        _apply_operations(job, [
            {'type': 'insert_header', 'text': 'H2 as string', 'level': 'h2'},
            {'type': 'insert_header', 'text': 'H3 as string', 'level': 'H3'},
            {
                'type': 'insert_header',
                'text': 'Fallback',
                'level': 'bad-level',
            },
        ])

        levels = list(
            self.note.headers.order_by('order').values_list('level', flat=True)
        )
        self.assertEqual(levels, [2, 3, 2])

    def test_normalize_operations_maps_aliases_and_text_fallback(self):
        operations = _normalize_operations([
            {'type': 'h2', 'title': 'Section title'},
            {'type': 'text', 'text': 'Plain paragraph'},
            {'type': 'insert_text', 'html': '<p>Ready html</p>'},
            {'type': 'unknown', 'text': 'skip me'},
        ])

        self.assertEqual(len(operations), 3)
        self.assertEqual(operations[0]['type'], 'insert_header')
        self.assertEqual(operations[0]['level'], 2)
        self.assertEqual(operations[1]['type'], 'insert_text')
        self.assertEqual(operations[1]['html'], '<p>Plain paragraph</p>')
        self.assertEqual(operations[2]['html'], '<p>Ready html</p>')

    @patch('apps.ai_writing.tasks.resolve_runtime')
    @patch('apps.ai_writing.tasks.get_provider_handler')
    def test_execute_generation_job_fails_when_no_applicable_operations(
        self,
        handler_mock,
        resolve_runtime_mock,
    ):
        runtime = {
            'global_config': type(
                'Config',
                (),
                {
                    'default_temperature': 0.7,
                    'default_max_tokens': 1200,
                },
            )(),
            'prompt_template': type(
                'Prompt',
                (),
                {
                    'system_prompt': 'system',
                    'user_prompt_template': 'template',
                },
            )(),
            'model': type('Model', (), {'code': 'test-model'})(),
            'provider': type('Provider', (), {'code': 'openai'})(),
            'credential': None,
        }
        resolve_runtime_mock.return_value = runtime
        handler_instance = handler_mock.return_value
        handler_instance.generate.return_value = {
            'operations': [
                {'type': 'unknown', 'text': 'ignored'},
            ]
        }

        job = AIGenerationJob.objects.create(
            owner=self.user,
            note=self.note,
            operation_type=OPERATION_WRITE_NOTE,
        )

        with self.assertRaises(ValueError):
            execute_generation_job.run(str(job.uuid))

        job.refresh_from_db()
        self.assertEqual(job.status, AIGenerationJob.STATUS_FAILED)
        self.assertIn('no applicable operations', job.error_message.lower())

        log = AIGenerationLog.objects.get(job=job)
        self.assertEqual(log.status, AIGenerationLog.STATUS_FAILED)
        self.assertIn('no applicable operations', log.error_message.lower())
        self.assertEqual(
            log.response_payload,
            {'operations': [{'type': 'unknown', 'text': 'ignored'}]},
        )
        self.assertEqual(log.normalized_operations, [])

        called_prompt = handler_instance.generate.call_args.kwargs['prompt']
        self.assertIn(OUTPUT_FORMAT_CONTRACT, called_prompt['system'])

    def test_execute_generation_job_succeeds_with_mock_runtime(self):
        job = AIGenerationJob.objects.create(
            owner=self.user,
            note=self.note,
            operation_type=OPERATION_WRITE_NOTE,
        )

        execute_generation_job.run(str(job.uuid))

        job.refresh_from_db()
        self.assertEqual(job.status, AIGenerationJob.STATUS_SUCCEEDED)
        self.assertEqual(job.result_payload['provider'], 'mock')
        self.assertGreater(self.note.headers.count(), 0)
        self.assertGreater(self.note.text_contents.count(), 0)

        log = AIGenerationLog.objects.get(job=job)
        self.assertEqual(log.status, AIGenerationLog.STATUS_SUCCEEDED)
        self.assertEqual(log.provider_code, 'mock')
        self.assertEqual(log.model_code, 'mock-v1')
        self.assertGreater(len(log.normalized_operations), 0)
