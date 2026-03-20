from django.contrib import admin

from .models import AIGenerationJob, AIGenerationLog


@admin.register(AIGenerationJob)
class AIGenerationJobAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'operation_type',
        'status',
        'owner',
        'note',
        'created_at',
    )
    list_filter = ('operation_type', 'status')
    search_fields = ('uuid', 'note__uuid', 'owner__username')
    readonly_fields = (
        'uuid',
        'created_at',
        'updated_at',
        'started_at',
        'finished_at',
        'celery_task_id',
    )


@admin.register(AIGenerationLog)
class AIGenerationLogAdmin(admin.ModelAdmin):
    list_display = (
        'uuid',
        'job',
        'operation_type',
        'provider_code',
        'model_code',
        'status',
        'created_at',
    )
    list_filter = ('status', 'operation_type', 'provider_code')
    search_fields = ('uuid', 'job__uuid', 'note__uuid', 'owner__username')
    readonly_fields = (
        'uuid',
        'job',
        'owner',
        'note',
        'operation_type',
        'provider_code',
        'model_code',
        'status',
        'celery_task_id',
        'request_prompt',
        'request_options',
        'request_context',
        'request_metadata',
        'response_payload',
        'normalized_operations',
        'result_metadata',
        'error_message',
        'started_at',
        'finished_at',
        'duration_ms',
        'created_at',
    )
