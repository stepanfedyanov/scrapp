"""Integration tests for blog defaults API endpoints."""
from typing import Any, cast

from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework import status

from apps.ai_writing.models import AIGenerationJob
from apps.ai_platform.constants import (
    OPERATION_WRITE_MORE_TEXT,
    OPERATION_WRITE_NEW_CHAPTER,
    OPERATION_WRITE_NOTE,
    OPERATION_WRITE_STRUCTURE,
)
from apps.integrations.models import IntegrationDefinition, PublishTarget
from blog.models import (
    Blog,
    BlogIntegrationDefault,
    Integration,
    Note,
    NoteHeader,
)

User = get_user_model()


class BlogDefaultIntegrationsAPITestCase(TestCase):
    """Test blog default integrations API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )
        self.blog = Blog.objects.create(
            owner=self.user,
            title='Test Blog',
        )
        self.definition = IntegrationDefinition.objects.create(
            code='test-integration',
            name='Test Integration',
            category='test',
            config_schema={},
            publish_schema={},
            handler_path='apps.integrations.handlers.webhook.webhook_handler',
        )
        self.integration = Integration.objects.create(
            owner=self.user,
            definition=self.definition,
            name='test-integration',
            title='Test Integration',
            provider='medium',
            credentials={'token': 'test-token'},
        )

        # Get auth token
        response = cast(
            Any,
            self.client.post('/api/auth/token/', {
                'username': 'testuser',
                'password': 'testpass123',
            }),
        )
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_list_blog_default_integrations(self):
        """Test listing blog default integrations."""
        # Create a default
        default = BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
            publish_settings={'target': 'https://example.com'},
            is_enabled=True,
        )

        # List defaults
        url = f'/api/blog-default-integrations/?blog_uuid={self.blog.uuid}'
        response = self.client.get(url)
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(payload, dict) and 'results' in payload:
            data = payload['results']
        else:
            data = payload
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], str(default.id))
        self.assertEqual(data[0]['is_enabled'], True)

    def test_create_blog_default_integration(self):
        """Test creating a blog default integration."""
        url = '/api/blog-default-integrations/'
        data = {
            'blog_uuid': self.blog.uuid,
            'integration_id': self.integration.pk,
            'publish_settings': {'target': 'https://example.com'},
            'is_enabled': True,
        }

        response = self.client.post(url, data, format='json')
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload['is_enabled'], True)

        # Verify created
        default = BlogIntegrationDefault.objects.get(
            blog=self.blog,
            integration=self.integration,
        )
        self.assertEqual(
            default.publish_settings['target'],
            'https://example.com',
        )

    def test_update_blog_default_integration(self):
        """Test updating a blog default integration."""
        default = BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
            publish_settings={'target': 'https://old.com'},
            is_enabled=True,
        )

        url = f'/api/blog-default-integrations/{default.id}/'
        data = {
            'blog_uuid': self.blog.uuid,
            'integration_id': self.integration.pk,
            'publish_settings': {'target': 'https://new.com'},
            'is_enabled': False,
        }

        response = self.client.patch(url, data, format='json')
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(payload['is_enabled'], False)

        # Verify updated
        default.refresh_from_db()
        self.assertEqual(default.publish_settings['target'], 'https://new.com')
        self.assertFalse(default.is_enabled)

    def test_delete_blog_default_integration(self):
        """Test deleting a blog default integration."""
        default = BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
        )

        url = f'/api/blog-default-integrations/{default.id}/'
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            BlogIntegrationDefault.objects.filter(id=default.id).exists()
        )

    def test_auto_create_publish_targets_on_note_creation(self):
        """Test that PublishTargets are auto-created when a note is created."""
        # Create a default integration
        BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
            publish_settings={'target': 'https://example.com'},
            is_enabled=True,
        )

        # Create a note
        url = '/api/notes/'
        data = {
            'blog_uuid': self.blog.uuid,
            'title': 'Test Note',
            'body': 'Test content',
        }

        response = self.client.post(url, data, format='json')
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        note_uuid = payload['uuid']

        # Check that PublishTarget was created
        targets = PublishTarget.objects.filter(object_id=note_uuid)
        self.assertEqual(targets.count(), 1)

        target = targets.get()
        self.assertEqual(target.integration, self.integration)
        self.assertEqual(
            target.publish_settings['target'],
            'https://example.com',
        )
        self.assertTrue(target.is_enabled)
        self.assertEqual(target.status, PublishTarget.STATUS_DRAFT)

    def test_permission_denied_for_other_user(self):
        """Test that other users cannot access blog defaults."""
        User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123',
        )

        # Create new client for other user
        other_client = APIClient()
        token_response = cast(
            Any,
            other_client.post('/api/auth/token/', {
                'username': 'otheruser',
                'password': 'otherpass123',
            }),
        )
        other_token = token_response.json()['access']
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token}')

        # Try to list defaults for another user's blog
        url = f'/api/blog-default-integrations/?blog_uuid={self.blog.uuid}'
        response = cast(Any, other_client.get(url))
        payload = response.json()

        # Should return empty list (no defaults visible)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if isinstance(payload, dict) and 'results' in payload:
            data = payload['results']
        else:
            data = payload
        self.assertEqual(len(data), 0)


class AIWritingAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='ai-user',
            email='ai@example.com',
            password='testpass123',
        )
        self.other_user = User.objects.create_user(
            username='other-ai-user',
            email='other-ai@example.com',
            password='testpass123',
        )
        self.blog = Blog.objects.create(owner=self.user, title='AI Blog')
        self.note = Note.objects.create(
            blog=self.blog,
            title='AI Note',
            body='',
        )
        self.other_blog = Blog.objects.create(
            owner=self.other_user,
            title='Other Blog',
        )
        self.other_note = Note.objects.create(
            blog=self.other_blog,
            title='Other Note',
            body='',
        )

        token_response = cast(
            Any,
            self.client.post('/api/auth/token/', {
                'username': 'ai-user',
                'password': 'testpass123',
            }),
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {token_response.json()['access']}"
            )
        )

    def _assert_job_created(self, response, operation_type):
        payload = response.json()
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(payload['operation_type'], operation_type)
        self.assertEqual(
            payload['status'],
            AIGenerationJob.STATUS_QUEUED,
        )
        self.assertTrue(
            AIGenerationJob.objects.filter(
                uuid=payload['job_uuid']
            ).exists()
        )

    @patch('apps.ai_writing.services.jobs.execute_generation_job.delay')
    def test_write_structure_creates_job_for_empty_note(self, delay_mock):
        response = self.client.post(
            f'/api/notes/{self.note.uuid}/ai/write-structure/',
            {},
            format='json',
        )

        self._assert_job_created(response, OPERATION_WRITE_STRUCTURE)
        delay_mock.assert_called_once()

    @patch('apps.ai_writing.services.jobs.execute_generation_job.delay')
    def test_write_note_rejects_non_empty_note(self, delay_mock):
        NoteHeader.objects.create(
            note=self.note,
            text='Existing',
            level=2,
            order=0,
        )

        response = self.client.post(
            f'/api/notes/{self.note.uuid}/ai/write-note/',
            {},
            format='json',
        )
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            payload['detail'],
            'This action is allowed only for empty notes.',
        )
        delay_mock.assert_not_called()

    @patch('apps.ai_writing.services.jobs.execute_generation_job.delay')
    def test_write_new_chapter_requires_source_block(self, delay_mock):
        response = self.client.post(
            f'/api/notes/{self.note.uuid}/ai/write-new-chapter/',
            {},
            format='json',
        )
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            payload['detail'],
            'source_block_uuid is required.',
        )
        delay_mock.assert_not_called()

    @patch('apps.ai_writing.services.jobs.execute_generation_job.delay')
    def test_write_new_chapter_rejects_foreign_source_block(self, delay_mock):
        foreign_header = NoteHeader.objects.create(
            note=self.other_note,
            text='Foreign',
            level=2,
            order=0,
        )

        response = self.client.post(
            f'/api/notes/{self.note.uuid}/ai/write-new-chapter/',
            {'source_block_uuid': str(foreign_header.uuid)},
            format='json',
        )
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            payload['detail'],
            'source_block_uuid does not belong to this note.',
        )
        delay_mock.assert_not_called()

    @patch('apps.ai_writing.services.jobs.execute_generation_job.delay')
    def test_write_more_text_creates_job_with_source_block(self, delay_mock):
        header = NoteHeader.objects.create(
            note=self.note,
            text='Section',
            level=2,
            order=0,
        )

        response = self.client.post(
            f'/api/notes/{self.note.uuid}/ai/write-more-text/',
            {'source_block_uuid': str(header.uuid)},
            format='json',
        )
        payload = response.json()

        self._assert_job_created(response, OPERATION_WRITE_MORE_TEXT)
        job = AIGenerationJob.objects.get(uuid=payload['job_uuid'])
        self.assertEqual(job.source_block_uuid, header.uuid)
        delay_mock.assert_called_once()

    def test_ai_generation_jobs_list_is_scoped_to_owner(self):
        own_job = AIGenerationJob.objects.create(
            owner=self.user,
            note=self.note,
            operation_type=OPERATION_WRITE_NOTE,
        )
        AIGenerationJob.objects.create(
            owner=self.other_user,
            note=self.other_note,
            operation_type=OPERATION_WRITE_NOTE,
        )

        response = self.client.get(
            f'/api/ai-generation-jobs/?note_uuid={self.note.uuid}'
        )
        payload = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]['uuid'], str(own_job.uuid))

    def test_ai_generation_job_retrieve_denies_other_user_job(self):
        foreign_job = AIGenerationJob.objects.create(
            owner=self.other_user,
            note=self.other_note,
            operation_type=OPERATION_WRITE_NEW_CHAPTER,
        )

        response = self.client.get(
            f'/api/ai-generation-jobs/{foreign_job.uuid}/'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
