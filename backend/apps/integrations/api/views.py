from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.integrations.services import publish_service
from apps.integrations.api.serializers import (
    IntegrationDefinitionSerializer,
    IntegrationSerializer,
    PublishLogSerializer,
    PublishTargetSerializer,
)
from apps.integrations.models import (
    IntegrationDefinition,
    PublishTarget,
)
from blog.models import Integration
from blog.permissions import IsOwner


class IntegrationDefinitionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only viewset for active integration definitions."""

    queryset = (
        IntegrationDefinition.objects.filter(is_active=True)
        .order_by('name')
    )
    serializer_class = IntegrationDefinitionSerializer
    permission_classes = [IsAuthenticated]


class IntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = IntegrationSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self) -> QuerySet[Any]:
        qs = Integration.objects.alive().filter(owner=self.request.user)
        qs = qs.select_related('definition')
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def perform_create(self, serializer: IntegrationSerializer) -> None:
        serializer.save(owner=self.request.user)


class PublishTargetViewSet(viewsets.ModelViewSet):
    serializer_class = PublishTargetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Any]:
        qs = PublishTarget.objects.select_related('integration__definition')
        # restrict to user's integrations
        qs = qs.filter(integration__owner=self.request.user)
        ct = self.request.query_params.get('content_type')
        if ct:
            # allow either id or model name
            if ct.isdigit():
                qs = qs.filter(content_type_id=int(ct))
            else:
                qs = qs.filter(content_type__model=ct)
        obj_id = self.request.query_params.get('object_id')
        if obj_id:
            qs = qs.filter(object_id=obj_id)
        return qs

    def perform_create(self, serializer: PublishTargetSerializer) -> None:
        # serializer.validate_integration already checks owner
        serializer.save()

    @action(detail=True, methods=['post'])
    def publish(self, request: Request, pk: Any = None) -> Response:
        target = self.get_object()
        if not target.is_enabled:
            return Response({'detail': 'Target is disabled'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            publish_service.publish_target(target, request.data or {})
        except Exception:  # log internally
            return Response({'detail': 'internal error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer = self.get_serializer(target)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def logs(self, request: Request, pk: Any = None) -> Response:
        target = self.get_object()
        logs = target.logs.order_by('-created_at')
        page = self.paginate_queryset(logs)
        serializer = PublishLogSerializer(page or logs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
