import uuid

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import models

from .constants import OPERATION_CHOICES
from .security import decrypt_secret, encrypt_secret, mask_secret


class AIProviderDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    handler_path = models.CharField(max_length=500)
    capabilities = models.JSONField(default=dict, blank=True)
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True, db_index=True)
    version = models.CharField(max_length=32, default='1.0')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority', 'name']

    def __str__(self):
        return f'{self.name} ({self.code})'


class AIModelDefinition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        AIProviderDefinition,
        on_delete=models.CASCADE,
        related_name='models',
    )
    code = models.CharField(max_length=120)
    display_name = models.CharField(max_length=200)
    max_context_tokens = models.PositiveIntegerField(default=4096)
    max_output_tokens = models.PositiveIntegerField(default=2048)
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider__priority', 'priority', 'display_name']
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'code'],
                name='ai_model_unique_provider_code',
            )
        ]

    def __str__(self):
        return f'{self.display_name} ({self.code})'


class AIProviderCredential(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        AIProviderDefinition,
        on_delete=models.CASCADE,
        related_name='credentials',
    )
    api_key_encrypted = models.TextField(blank=True)
    base_url = models.URLField(blank=True)
    organization = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['provider'],
                name='ai_credential_unique_provider',
            )
        ]

    @property
    def api_key(self):
        return decrypt_secret(self.api_key_encrypted)

    @api_key.setter
    def api_key(self, value):
        self.api_key_encrypted = encrypt_secret(value)

    @property
    def api_key_masked(self):
        try:
            return mask_secret(self.api_key)
        except InvalidToken:
            return '[invalid encrypted key]'

    def clean(self):
        if not self.api_key_encrypted:
            raise ValidationError(
                {'api_key_encrypted': 'API key is required.'}
            )

    def __str__(self):
        return f'Credential for {self.provider.code}'


class AIGlobalConfig(models.Model):
    SINGLETON_ID = 1

    singleton_id = models.PositiveSmallIntegerField(
        default=SINGLETON_ID,
        unique=True,
        editable=False,
    )
    request_timeout_seconds = models.PositiveIntegerField(default=60)
    retry_count = models.PositiveIntegerField(default=2)
    retry_backoff_seconds = models.PositiveIntegerField(default=3)
    max_parallel_tasks = models.PositiveIntegerField(default=4)
    queue_name = models.CharField(max_length=64, default='ai')
    default_temperature = models.FloatField(default=0.7)
    default_max_tokens = models.PositiveIntegerField(default=1200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.singleton_id = self.SINGLETON_ID
        super().save(*args, **kwargs)

    def __str__(self):
        return 'AI Global Config'


class AIPromptTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=120, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    operation_type = models.CharField(max_length=64, choices=OPERATION_CHOICES)
    system_prompt = models.TextField()
    user_prompt_template = models.TextField()
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True, db_index=True)
    version = models.CharField(max_length=32, default='1.0')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['operation_type', 'priority', 'name']

    def __str__(self):
        return f'{self.name} ({self.operation_type})'
