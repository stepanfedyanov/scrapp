from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.ai_platform.constants import (
    OPERATION_WRITE_MORE_TEXT,
    OPERATION_WRITE_NEW_CHAPTER,
    OPERATION_WRITE_NOTE,
    OPERATION_WRITE_STRUCTURE,
)
from apps.ai_writing.permissions import HasAIAccess
from apps.ai_writing.services.jobs import create_generation_job
from apps.integrations.services.note_creation_service import (
    create_publish_targets_from_defaults,
)
from .models import (
    Blog,
    BlogIntegration,
    BlogIntegrationDefault,
    Integration,
    Note,
    NoteHeader,
    NoteIntegration,
    NoteTextContent,
)
from .permissions import IsOwner
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response({
        'id': request.user.pk,
        'username': request.user.username,
        'email': request.user.email,
        'can_use_ai': request.user.has_perm('ai_writing.can_use_ai'),
    })


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

    def _create_ai_job(
        self,
        request,
        note,
        operation_type,
        require_source_block=False,
    ):
        if not HasAIAccess().has_permission(request, self):
            return Response(
                {'detail': HasAIAccess.message},
                status=status.HTTP_403_FORBIDDEN,
            )

        source_block_uuid = request.data.get('source_block_uuid')
        if require_source_block and not source_block_uuid:
            return Response(
                {'detail': 'source_block_uuid is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if source_block_uuid:
            is_in_note = NoteTextContent.objects.filter(
                note=note,
                uuid=source_block_uuid,
            ).exists() or NoteHeader.objects.filter(
                note=note,
                uuid=source_block_uuid,
            ).exists()
            if not is_in_note:
                return Response(
                    {
                        'detail': (
                            'source_block_uuid does not belong to this note.'
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if operation_type in (OPERATION_WRITE_STRUCTURE, OPERATION_WRITE_NOTE):
            has_content = (
                note.headers.exists()
                or note.text_contents.exists()
                or bool(note.body.strip())
            )
            if has_content:
                return Response(
                    {'detail': 'This action is allowed only for empty notes.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        idempotency_key = request.headers.get('Idempotency-Key', '').strip()
        job = create_generation_job(
            owner=request.user,
            note=note,
            operation_type=operation_type,
            source_block_uuid=source_block_uuid,
            request_payload=request.data,
            idempotency_key=idempotency_key,
        )

        return Response(
            {
                'job_uuid': str(job.uuid),
                'status': job.status,
                'operation_type': job.operation_type,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=['post'], url_path='ai/write-structure')
    def ai_write_structure(self, request, *args, **kwargs):
        note = self.get_object()
        return self._create_ai_job(request, note, OPERATION_WRITE_STRUCTURE)

    @action(detail=True, methods=['post'], url_path='ai/write-note')
    def ai_write_note(self, request, *args, **kwargs):
        note = self.get_object()
        return self._create_ai_job(request, note, OPERATION_WRITE_NOTE)

    @action(detail=True, methods=['post'], url_path='ai/write-new-chapter')
    def ai_write_new_chapter(self, request, *args, **kwargs):
        note = self.get_object()
        return self._create_ai_job(
            request,
            note,
            OPERATION_WRITE_NEW_CHAPTER,
            require_source_block=True,
        )

    @action(detail=True, methods=['post'], url_path='ai/write-more-text')
    def ai_write_more_text(self, request, *args, **kwargs):
        note = self.get_object()
        return self._create_ai_job(
            request,
            note,
            OPERATION_WRITE_MORE_TEXT,
            require_source_block=True,
        )


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
        if (
            blog.owner_id != self.request.user.id
            or integration.owner_id != self.request.user.id
        ):
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
