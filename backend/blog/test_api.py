"""Integration tests for blog defaults API endpoints."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.integrations.models import IntegrationDefinition, PublishTarget
from blog.models import Blog, Integration, BlogIntegrationDefault, Note

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
        response = self.client.post('/api/auth/token/', {
            'username': 'testuser',
            'password': 'testpass123',
        })
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
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # response.data is a list when pagination is applied
        if isinstance(response.data, dict) and 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['id'], str(default.id))
        self.assertEqual(data[0]['is_enabled'], True)

    def test_create_blog_default_integration(self):
        """Test creating a blog default integration."""
        url = '/api/blog-default-integrations/'
        data = {
            'blog_uuid': self.blog.uuid,
            'integration_id': self.integration.id,
            'publish_settings': {'target': 'https://example.com'},
            'is_enabled': True,
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['is_enabled'], True)
        
        # Verify created
        default = BlogIntegrationDefault.objects.get(
            blog=self.blog,
            integration=self.integration,
        )
        self.assertEqual(default.publish_settings['target'], 'https://example.com')

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
            'integration_id': self.integration.id,
            'publish_settings': {'target': 'https://new.com'},
            'is_enabled': False,
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['is_enabled'], False)
        
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
        self.assertFalse(BlogIntegrationDefault.objects.filter(id=default.id).exists())

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
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        note_uuid = response.data['uuid']
        
        # Check that PublishTarget was created
        targets = PublishTarget.objects.filter(object_id=note_uuid)
        self.assertEqual(targets.count(), 1)
        
        target = targets.first()
        self.assertEqual(target.integration, self.integration)
        self.assertEqual(target.publish_settings['target'], 'https://example.com')
        self.assertTrue(target.is_enabled)
        self.assertEqual(target.status, PublishTarget.STATUS_DRAFT)

    def test_permission_denied_for_other_user(self):
        """Test that other users cannot access blog defaults."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123',
        )
        
        # Create new client for other user
        other_client = APIClient()
        response = other_client.post('/api/auth/token/', {
            'username': 'otheruser',
            'password': 'otherpass123',
        })
        other_token = response.data['access']
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token}')
        
        # Try to list defaults for another user's blog
        url = f'/api/blog-default-integrations/?blog_uuid={self.blog.uuid}'
        response = other_client.get(url)
        
        # Should return empty list (no defaults visible)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # response.data is a list when pagination is applied
        if isinstance(response.data, dict) and 'results' in response.data:
            data = response.data['results']
        else:
            data = response.data
        self.assertEqual(len(data), 0)
