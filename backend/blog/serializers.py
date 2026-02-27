from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Blog, Note, Integration, BlogIntegration, NoteIntegration, NoteHeader, NoteTextContent
from apps.integrations.models import IntegrationDefinition

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        return user

class IntegrationSerializer(serializers.ModelSerializer):
    definition = serializers.PrimaryKeyRelatedField(
        queryset=IntegrationDefinition.objects.all(),
        required=False,
    )

    class Meta:
        model = Integration
        fields = (
            'id',
            'name',
            'title',
            'provider',
            'definition',
            'config',
            'credentials',
            'status',
            'last_error',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class BlogIntegrationSerializer(serializers.ModelSerializer):
    integration = IntegrationSerializer(read_only=True)
    integration_id = serializers.PrimaryKeyRelatedField(
        source='integration',
        queryset=Integration.objects.alive(),
        write_only=True,
    )
    blog_id = serializers.PrimaryKeyRelatedField(
        source='blog',
        queryset=Blog.objects.alive(),
        write_only=True,
    )

    class Meta:
        model = BlogIntegration
        fields = (
            'id',
            'blog_id',
            'integration',
            'integration_id',
            'enabled',
            'settings',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class NoteIntegrationSerializer(serializers.ModelSerializer):
    integration = IntegrationSerializer(read_only=True)
    integration_id = serializers.PrimaryKeyRelatedField(
        source='integration',
        queryset=Integration.objects.alive(),
        write_only=True,
    )
    note_id = serializers.PrimaryKeyRelatedField(
        source='note', queryset=Note.objects.alive(), write_only=True
    )

    class Meta:
        model = NoteIntegration
        fields = (
            'id',
            'note_id',
            'integration',
            'integration_id',
            'enabled',
            'use_blog_defaults',
            'settings',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class BlogSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    blog_integrations = BlogIntegrationSerializer(many=True, read_only=True)

    class Meta:
        model = Blog
        fields = (
            'id',
            'uuid',
            'title',
            'owner',
            'blog_integrations',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class NoteHeaderSerializer(serializers.ModelSerializer):
    note_uuid = serializers.SlugRelatedField(
        source='note',
        slug_field='uuid',
        queryset=Note.objects.alive(),
        write_only=True,
    )

    class Meta:
        model = NoteHeader
        fields = ('uuid', 'note_uuid', 'text', 'level', 'order', 'created_at', 'updated_at')
        read_only_fields = ('uuid', 'created_at', 'updated_at')


class NoteTextContentSerializer(serializers.ModelSerializer):
    note_uuid = serializers.SlugRelatedField(
        source='note',
        slug_field='uuid',
        queryset=Note.objects.alive(),
        write_only=True,
    )

    class Meta:
        model = NoteTextContent
        fields = ('uuid', 'note_uuid', 'html', 'order', 'created_at', 'updated_at')
        read_only_fields = ('uuid', 'created_at', 'updated_at')


class NoteSerializer(serializers.ModelSerializer):
    blog = BlogSerializer(read_only=True)
    blog_uuid = serializers.SlugRelatedField(
        source='blog',
        slug_field='uuid',
        queryset=Blog.objects.alive(),
        write_only=True,
    )
    note_integrations = NoteIntegrationSerializer(many=True, read_only=True)
    headers = NoteHeaderSerializer(many=True, read_only=True)
    text_contents = NoteTextContentSerializer(many=True, read_only=True)

    class Meta:
        model = Note
        fields = (
            'id',
            'uuid',
            'blog',
            'blog_uuid',
            'title',
            'body',
            'status',
            'scheduled_at',
            'published_at',
            'archived_at',
            'note_integrations',
            'headers',
            'text_contents',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, attrs):
        status = attrs.get('status')
        scheduled_at = attrs.get('scheduled_at')
        if status == Note.STATUS_SCHEDULED and not scheduled_at:
            raise serializers.ValidationError(
                {'scheduled_at': 'Required for scheduled notes.'}
            )
        return attrs

    def update(self, instance, validated_data):
        status = validated_data.get('status')
        if status == Note.STATUS_PUBLISHED and instance.published_at is None:
            instance.published_at = timezone.now()
        if status == Note.STATUS_ARCHIVED and instance.archived_at is None:
            instance.archived_at = timezone.now()
        return super().update(instance, validated_data)
