import uuid

from django.conf import settings
from django.db import models

from apps.ai_platform.constants import OPERATION_CHOICES


class AIGenerationJob(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_RUNNING = 'running'
    STATUS_SUCCEEDED = 'succeeded'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued'),
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCEEDED, 'Succeeded'),
        (STATUS_FAILED, 'Failed'),
    ]

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_generation_jobs',
    )
    note = models.ForeignKey(
        'blog.Note',
        on_delete=models.CASCADE,
        related_name='ai_generation_jobs',
    )
    operation_type = models.CharField(max_length=64, choices=OPERATION_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_QUEUED,
        db_index=True,
    )
    source_block_uuid = models.UUIDField(null=True, blank=True)
    request_payload = models.JSONField(default=dict, blank=True)
    result_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    celery_task_id = models.CharField(max_length=64, blank=True)
    idempotency_key = models.CharField(
        max_length=120,
        blank=True,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['note', 'created_at']),
            models.Index(fields=['owner', 'created_at']),
        ]
        permissions = [
            ('can_use_ai', 'Can use AI features'),
        ]

    def __str__(self):
        return f'{self.operation_type} ({self.status})'


class AIGenerationLog(models.Model):
    STATUS_RUNNING = 'running'
    STATUS_SUCCEEDED = 'succeeded'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_RUNNING, 'Running'),
        (STATUS_SUCCEEDED, 'Succeeded'),
        (STATUS_FAILED, 'Failed'),
    ]

    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    job = models.ForeignKey(
        AIGenerationJob,
        on_delete=models.CASCADE,
        related_name='logs',
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_generation_logs',
    )
    note = models.ForeignKey(
        'blog.Note',
        on_delete=models.CASCADE,
        related_name='ai_generation_logs',
    )
    operation_type = models.CharField(max_length=64, choices=OPERATION_CHOICES)
    provider_code = models.CharField(max_length=100, blank=True)
    model_code = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_RUNNING,
        db_index=True,
    )
    celery_task_id = models.CharField(max_length=64, blank=True)
    request_prompt = models.JSONField(default=dict, blank=True)
    request_options = models.JSONField(default=dict, blank=True)
    request_context = models.JSONField(default=dict, blank=True)
    request_metadata = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    normalized_operations = models.JSONField(default=list, blank=True)
    result_metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'created_at']),
            models.Index(fields=['note', 'created_at']),
            models.Index(fields=['job', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f'Log {self.operation_type} ({self.status})'
