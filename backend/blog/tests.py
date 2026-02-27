from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from .models import Blog, Note

User = get_user_model()


class NoteAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='pass')
        self.client.force_authenticate(self.user)
        self.blog = Blog.objects.create(owner=self.user, title='B')

    def test_create_note_with_blank_title(self):
        url = reverse('notes-list')
        resp = self.client.post(url, {'blog_uuid': self.blog.uuid, 'title': '', 'body': ''}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['title'], '')

    def test_update_note_to_blank_title(self):
        note = Note.objects.create(blog=self.blog, title='foo')
        url = reverse('notes-detail', kwargs={'uuid': note.uuid})
        resp = self.client.patch(url, {'title': ''}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['title'], '')
