from __future__ import annotations

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.integrations.models import (
    IntegrationDefinition,
    PublishTarget,
    PublishLog,
)
from blog.models import Integration


class IntegrationDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationDefinition
        fields = (
            'id',
            'code',
            'name',
            'category',
            'description',
            'config_schema',
            'publish_schema',
            'version',
        )
        read_only_fields = fields


class IntegrationNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = ('id', 'title', 'definition')
        depth = 1  # will include definition id,name,code


class IntegrationSerializer(serializers.ModelSerializer):
    # nested read-only representation
    definition = IntegrationDefinitionSerializer(read_only=True)
    definition_id = serializers.PrimaryKeyRelatedField(
        source='definition',
        queryset=IntegrationDefinition.objects.filter(is_active=True),
        write_only=True,
        required=True,
    )

    class Meta:
        model = Integration
        fields = (
            'id',
            'title',
            'definition',
            'definition_id',
            'credentials',
            'status',
            'last_error',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at', 'last_error')

    # credentials validation has been moved to validate()

    def validate(self, attrs):
        # ensure definition is active
        definition = attrs.get('definition') or getattr(self.instance, 'definition', None)
        if definition and not definition.is_active:
            raise ValidationError({'definition_id': 'Selected integration definition is not active.'})
        # validate credentials schema if provided
        creds = attrs.get('credentials')
        if definition and creds is not None:
            schema = definition.config_schema or {}
            if schema:
                try:
                    import jsonschema

                    jsonschema.validate(instance=creds, schema=schema)
                except ImportError:  # no dependency, skip
                    pass
                except Exception as exc:
                    raise ValidationError({'credentials': f'invalid: {exc}'})
        return super().validate(attrs)

    def create(self, validated_data):
        # owner will be set in view
        return super().create(validated_data)


class PublishTargetSerializer(serializers.ModelSerializer):
    integration = IntegrationNestedSerializer(read_only=True)
    integration_id = serializers.PrimaryKeyRelatedField(
        source='integration',
        queryset=Integration.objects.all(),
        write_only=True,
        required=True,
    )
    content_type_id = serializers.PrimaryKeyRelatedField(
        source='content_type',
        queryset=ContentType.objects.all(),
        write_only=True,
        required=True,
    )
    object_id = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = PublishTarget
        fields = (
            'id',
            'integration',
            'integration_id',
            'content_type_id',
            'object_id',
            'publish_settings',
            'is_enabled',
            'status',
            'scheduled_at',
            'last_published_at',
            'retry_count',
            'last_error',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'last_published_at',
            'retry_count',
            'last_error',
            'created_at',
            'updated_at',
        )

    def validate_integration(self, value: Integration) -> Integration:
        user = self.context['request'].user
        if value.owner != user:
            raise ValidationError('Integration does not belong to the current user.')
        return value

    def validate(self, attrs):
        # ensure integration ownership
        integration = attrs.get('integration')
        if integration and integration.owner != self.context['request'].user:
            raise ValidationError({'integration_id': 'Integration does not belong to the current user.'})
        # object_id must be provided as valid UUID string
        obj = attrs.get('object_id')
        if obj is None or str(obj) == '':
            raise ValidationError({'object_id': 'This field is required.'})
        try:
            import uuid

            uuid.UUID(str(obj))
        except Exception:
            raise ValidationError({'object_id': 'Must be a valid UUID.'})
        return super().validate(attrs)


class PublishLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublishLog
        fields = (
            'id',
            'status',
            'error_message',
            'request_payload',
            'response_payload',
            'created_at',
        )
        read_only_fields = fields
