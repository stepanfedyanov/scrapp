from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Blog, Note, Integration, BlogIntegration, NoteIntegration, NoteHeader, NoteTextContent, BlogIntegrationDefault
from .permissions import IsOwner
from apps.integrations.services.note_creation_service import create_publish_targets_from_defaults
from .serializers import (
    BlogIntegrationSerializer,
    BlogSerializer,
    IntegrationSerializer,
    NoteHeaderSerializer,
    NoteIntegrationSerializer,
    NoteSerializer,
    NoteTextContentSerializer,
    RegisterSerializer,
    BlogIntegrationDefaultSerializer,
)


class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class BlogViewSet(viewsets.ModelViewSet):
    serializer_class = BlogSerializer
    permission_classes = [IsOwner]
    lookup_field = 'uuid'

    def get_queryset(self):
        return Blog.objects.alive().filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        blog = self.get_object()
        blog.is_deleted = True
        blog.deleted_at = timezone.now()
        blog.save(update_fields=['is_deleted', 'deleted_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [IsOwner]
    lookup_field = 'uuid'

    def get_queryset(self):
        queryset = (
            Note.objects.alive()
            .filter(blog__owner=self.request.user)
            .select_related('blog')
            .prefetch_related('headers', 'text_contents')
        )
        blog_uuid = self.request.query_params.get('blog_uuid')
        if blog_uuid:
            queryset = queryset.filter(blog__uuid=blog_uuid)
        return queryset

    def perform_create(self, serializer):
        blog = serializer.validated_data['blog']
        if blog.owner_id != self.request.user.id:
            raise PermissionDenied('Invalid blog owner')
        note = serializer.save()
        # Auto-create publish targets from blog defaults
        create_publish_targets_from_defaults(note)

    def destroy(self, request, *args, **kwargs):
        note = self.get_object()
        note.status = Note.STATUS_DELETED
        note.is_deleted = True
        note.deleted_at = timezone.now()
        note.save(update_fields=['status', 'is_deleted', 'deleted_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def archive(self, request, *args, **kwargs):
        note = self.get_object()
        note.status = Note.STATUS_ARCHIVED
        note.archived_at = timezone.now()
        note.save(update_fields=['status', 'archived_at'])
        serializer = self.get_serializer(note)
        return Response(serializer.data)


class IntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = IntegrationSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return Integration.objects.alive().filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        integration = self.get_object()
        integration.is_deleted = True
        integration.deleted_at = timezone.now()
        integration.save(update_fields=['is_deleted', 'deleted_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class BlogIntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = BlogIntegrationSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return (
            BlogIntegration.objects.alive()
            .filter(blog__owner=self.request.user)
            .select_related('blog', 'integration')
        )

    def perform_create(self, serializer):
        blog = serializer.validated_data['blog']
        integration = serializer.validated_data['integration']
        if blog.owner_id != self.request.user.id or integration.owner_id != self.request.user.id:
            raise PermissionDenied('Invalid integration owner')
        serializer.save(blog=blog)

    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        record.is_deleted = True
        record.deleted_at = timezone.now()
        record.save(update_fields=['is_deleted', 'deleted_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class NoteIntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = NoteIntegrationSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return (
            NoteIntegration.objects.alive()
            .filter(note__blog__owner=self.request.user)
            .select_related('note', 'integration')
        )

    def perform_create(self, serializer):
        note = serializer.validated_data['note']
        integration = serializer.validated_data['integration']
        if (
            note.blog.owner_id != self.request.user.id
            or integration.owner_id != self.request.user.id
        ):
            raise PermissionDenied('Invalid note or integration owner')
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        record = self.get_object()
        record.is_deleted = True
        record.deleted_at = timezone.now()
        record.save(update_fields=['is_deleted', 'deleted_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class NoteHeaderViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = NoteHeaderSerializer
    permission_classes = [IsOwner]
    lookup_field = 'uuid'

    def get_queryset(self):
        queryset = NoteHeader.objects.filter(
            note__blog__owner=self.request.user
        ).select_related('note__blog')
        note_uuid = self.request.query_params.get('note_uuid')
        if note_uuid:
            queryset = queryset.filter(note__uuid=note_uuid)
        return queryset

    def perform_create(self, serializer):
        note = serializer.validated_data['note']
        if note.blog.owner_id != self.request.user.id:
            raise PermissionDenied('Invalid note owner')
        serializer.save()


class NoteTextContentViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = NoteTextContentSerializer
    permission_classes = [IsOwner]
    lookup_field = 'uuid'

    def get_queryset(self):
        queryset = NoteTextContent.objects.filter(
            note__blog__owner=self.request.user
        ).select_related('note__blog')
        note_uuid = self.request.query_params.get('note_uuid')
        if note_uuid:
            queryset = queryset.filter(note__uuid=note_uuid)
        return queryset

    def perform_create(self, serializer):
        note = serializer.validated_data['note']
        if note.blog.owner_id != self.request.user.id:
            raise PermissionDenied('Invalid note owner')
        serializer.save()


class BlogIntegrationDefaultViewSet(viewsets.ModelViewSet):
    """ViewSet for managing default integrations for a blog.
    
    Supports filtering by blog_uuid query parameter:
    GET    /api/blog-default-integrations/?blog_uuid={uuid}
    POST   /api/blog-default-integrations/
    PATCH  /api/blog-default-integrations/{id}/
    DELETE /api/blog-default-integrations/{id}/
    """
    serializer_class = BlogIntegrationDefaultSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        """Filter to user's integrations only."""
        queryset = (
            BlogIntegrationDefault.objects
            .filter(blog__owner=self.request.user)
            .select_related('blog', 'integration')
        )
        # Allow filtering by blog_uuid
        blog_uuid = self.request.query_params.get('blog_uuid')
        if blog_uuid:
            queryset = queryset.filter(blog__uuid=blog_uuid)
        return queryset

    def perform_create(self, serializer):
        """Ensure blog belongs to user and integration is owned by user."""
        blog_uuid = self.request.data.get('blog_uuid')
        if not blog_uuid:
            raise PermissionDenied('blog_uuid is required')
        
        try:
            blog = Blog.objects.get(uuid=blog_uuid, owner=self.request.user)
        except Blog.DoesNotExist:
            raise PermissionDenied('Invalid blog')
        
        integration = serializer.validated_data['integration']
        if integration.owner_id != self.request.user.id:
            raise PermissionDenied('Invalid integration owner')
        
        serializer.save(blog=blog)

    def perform_update(self, serializer):
        """Validate ownership on update."""
        integration = serializer.validated_data.get('integration')
        if integration and integration.owner_id != self.request.user.id:
            raise PermissionDenied('Invalid integration owner')
        serializer.save()
