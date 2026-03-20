from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.integrations.models import IntegrationDefinition, PublishTarget
from apps.integrations.services.note_creation_service import (
    create_publish_targets_from_defaults,
)
from blog.models import Blog, Integration, BlogIntegrationDefault, Note

User = get_user_model()


class BlogIntegrationDefaultTestCase(TestCase):
    """Test blog default integrations."""

    def setUp(self):
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

    def test_create_blog_default_integration(self):
        """Test creating a blog default integration."""
        default = BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
            publish_settings={'target': 'https://example.com'},
            is_enabled=True,
        )

        self.assertEqual(default.blog, self.blog)
        self.assertEqual(default.integration, self.integration)
        self.assertEqual(
            default.publish_settings['target'],
            'https://example.com',
        )
        self.assertTrue(default.is_enabled)

    def test_unique_constraint_blog_integration(self):
        """Test that blog + integration must be unique."""
        BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
        )

        with self.assertRaises(Exception):
            BlogIntegrationDefault.objects.create(
                blog=self.blog,
                integration=self.integration,
            )

    def test_auto_create_publish_targets_from_defaults(self):
        """Test that PublishTargets are auto-created when a Note is created."""
        BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
            publish_settings={'target': 'https://example1.com'},
            is_enabled=True,
        )

        integration2 = Integration.objects.create(
            owner=self.user,
            definition=self.definition,
            name='test-integration-2',
            title='Test Integration 2',
            provider='devto',
            credentials={'token': 'test-token-2'},
        )
        BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=integration2,
            publish_settings={'target': 'https://example2.com'},
            is_enabled=True,
        )

        note = Note.objects.create(
            blog=self.blog,
            title='Test Note',
            body='Test content',
        )

        targets = create_publish_targets_from_defaults(note)

        self.assertEqual(len(targets), 2)

        target1 = targets[0]
        self.assertEqual(target1.integration, self.integration)
        self.assertEqual(
            target1.publish_settings['target'],
            'https://example1.com',
        )
        self.assertTrue(target1.is_enabled)
        self.assertEqual(target1.status, PublishTarget.STATUS_DRAFT)
        self.assertEqual(target1.object_id, note.uuid)

        target2 = targets[1]
        self.assertEqual(target2.integration, integration2)
        self.assertEqual(
            target2.publish_settings['target'],
            'https://example2.com',
        )

    def test_no_targets_when_disabled_default(self):
        """Test that disabled defaults don't create targets."""
        BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
            is_enabled=False,
        )

        note = Note.objects.create(
            blog=self.blog,
            title='Test Note',
            body='Test content',
        )

        targets = create_publish_targets_from_defaults(note)

        self.assertEqual(len(targets), 0)

    def test_blog_changes_dont_affect_existing_notes(self):
        """Test that changes to blog defaults don't affect existing notes."""
        default = BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
        )

        note = Note.objects.create(
            blog=self.blog,
            title='Test Note',
            body='Test content',
        )
        create_publish_targets_from_defaults(note)

        content_type = ContentType.objects.get_for_model(Note)
        targets_before = PublishTarget.objects.filter(
            content_type=content_type,
            object_id=note.uuid,
        )
        self.assertEqual(targets_before.count(), 1)
        target_before = targets_before.first()
        if target_before is None:
            self.fail('Expected a publish target to be created')
        original_settings = target_before.publish_settings.copy()

        default.publish_settings = {'target': 'https://changed.com'}
        default.save()

        target_after = PublishTarget.objects.get(pk=target_before.pk)
        self.assertEqual(target_after.publish_settings, original_settings)

    def test_duplicate_target_prevention(self):
        """Test that duplicate targets are not created."""
        BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
        )

        note = Note.objects.create(
            blog=self.blog,
            title='Test Note',
            body='Test content',
        )
        targets1 = create_publish_targets_from_defaults(note)
        self.assertEqual(len(targets1), 1)

        targets2 = create_publish_targets_from_defaults(note)

        self.assertEqual(len(targets2), 0)

        content_type = ContentType.objects.get_for_model(Note)
        all_targets = PublishTarget.objects.filter(
            content_type=content_type,
            object_id=note.uuid,
        )
        self.assertEqual(all_targets.count(), 1)


class NoteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='pass')
        self.client.force_authenticate(self.user)
        self.blog = Blog.objects.create(owner=self.user, title='B')

    def test_create_note_with_blank_title(self):
        url = reverse('notes-list')
        resp = self.client.post(
            url,
            {'blog_uuid': self.blog.uuid, 'title': '', 'body': ''},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()['title'], '')

    def test_update_note_to_blank_title(self):
        note = Note.objects.create(blog=self.blog, title='foo')
        url = reverse('notes-detail', kwargs={'uuid': note.uuid})
        resp = self.client.patch(url, {'title': ''}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['title'], '')
