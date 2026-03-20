from rest_framework import mixins, viewsets

from .models import AIGenerationJob, AIGenerationLog
from .serializers import AIGenerationJobSerializer, AIGenerationLogSerializer
from blog.permissions import IsOwner


class AIGenerationJobViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AIGenerationJobSerializer
    permission_classes = [IsOwner]
    lookup_field = 'uuid'

    def get_queryset(self):
        queryset = (
            AIGenerationJob.objects
            .filter(owner=self.request.user)
            .select_related('note')
        )
        note_uuid = self.request.query_params.get('note_uuid')
        if note_uuid:
            queryset = queryset.filter(note__uuid=note_uuid)
        return queryset


class AIGenerationLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AIGenerationLogSerializer
    permission_classes = [IsOwner]
    lookup_field = 'uuid'

    def get_queryset(self):
        queryset = (
            AIGenerationLog.objects
            .filter(owner=self.request.user)
            .select_related('note', 'job')
        )
        note_uuid = self.request.query_params.get('note_uuid')
        if note_uuid:
            queryset = queryset.filter(note__uuid=note_uuid)

        job_uuid = self.request.query_params.get('job_uuid')
        if job_uuid:
            queryset = queryset.filter(job__uuid=job_uuid)

        return queryset
