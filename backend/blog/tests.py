from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from apps.integrations.models import IntegrationDefinition, PublishTarget
from blog.models import Blog, Integration, BlogIntegrationDefault, Note
from apps.integrations.services.note_creation_service import create_publish_targets_from_defaults

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
        self.assertEqual(default.publish_settings['target'], 'https://example.com')
        self.assertTrue(default.is_enabled)

    def test_unique_constraint_blog_integration(self):
        """Test that blog + integration must be unique."""
        BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            BlogIntegrationDefault.objects.create(
                blog=self.blog,
                integration=self.integration,
            )

    def test_auto_create_publish_targets_from_defaults(self):
        """Test that PublishTargets are auto-created when a Note is created."""
        # Create two default integrations for the blog
        default1 = BlogIntegrationDefault.objects.create(
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
        default2 = BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=integration2,
            publish_settings={'target': 'https://example2.com'},
            is_enabled=True,
        )
        
        # Create a note
        note = Note.objects.create(
            blog=self.blog,
            title='Test Note',
            body='Test content',
        )
        
        # Auto-create publish targets
        targets = create_publish_targets_from_defaults(note)
        
        # Should have created 2 targets
        self.assertEqual(len(targets), 2)
        
        # Check first target
        target1 = targets[0]
        self.assertEqual(target1.integration, self.integration)
        self.assertEqual(target1.publish_settings['target'], 'https://example1.com')
        self.assertTrue(target1.is_enabled)
        self.assertEqual(target1.status, PublishTarget.STATUS_DRAFT)
        # Verify the generic relation points to the note
        self.assertEqual(target1.object_id, note.uuid)
        
        # Check second target
        target2 = targets[1]
        self.assertEqual(target2.integration, integration2)
        self.assertEqual(target2.publish_settings['target'], 'https://example2.com')

    def test_no_targets_when_disabled_default(self):
        """Test that disabled defaults don't create targets."""
        # Create disabled default
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
        
        # Should have created 0 targets
        self.assertEqual(len(targets), 0)

    def test_blog_changes_dont_affect_existing_notes(self):
        """Test that changes to blog defaults don't affect existing notes."""
        # Create default integration
        default = BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
        )
        
        # Create note with auto-created targets
        note = Note.objects.create(
            blog=self.blog,
            title='Test Note',
            body='Test content',
        )
        create_publish_targets_from_defaults(note)
        
        # Get the created target
        content_type = ContentType.objects.get_for_model(Note)
        targets_before = PublishTarget.objects.filter(
            content_type=content_type,
            object_id=note.uuid,
        )
        self.assertEqual(targets_before.count(), 1)
        target_before = targets_before.first()
        original_settings = target_before.publish_settings.copy()
        
        # Now update the blog default
        default.publish_settings = {'target': 'https://changed.com'}
        default.save()
        
        # The existing note's target should NOT change
        target_after = PublishTarget.objects.get(pk=target_before.pk)
        self.assertEqual(target_after.publish_settings, original_settings)

    def test_duplicate_target_prevention(self):
        """Test that duplicate targets are not created."""
        # Create default integration
        BlogIntegrationDefault.objects.create(
            blog=self.blog,
            integration=self.integration,
        )
        
        # Create note and targets
        note = Note.objects.create(
            blog=self.blog,
            title='Test Note',
            body='Test content',
        )
        targets1 = create_publish_targets_from_defaults(note)
        self.assertEqual(len(targets1), 1)
        
        # Try to create targets again
        targets2 = create_publish_targets_from_defaults(note)
        
        # Should not create duplicates
        self.assertEqual(len(targets2), 0)
        
        # Total should still be 1
        content_type = ContentType.objects.get_for_model(Note)
        all_targets = PublishTarget.objects.filter(
            content_type=content_type,
            object_id=note.uuid,
        )
        self.assertEqual(all_targets.count(), 1)
