from rest_framework import serializers

from .models import AIGenerationJob, AIGenerationLog


class AIGenerationJobSerializer(serializers.ModelSerializer):
    note_uuid = serializers.UUIDField(source='note.uuid', read_only=True)

    class Meta:
        model = AIGenerationJob
        fields = (
            'uuid',
            'note_uuid',
            'operation_type',
            'status',
            'source_block_uuid',
            'request_payload',
            'result_payload',
            'error_message',
            'started_at',
            'finished_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class AIGenerationLogSerializer(serializers.ModelSerializer):
    note_uuid = serializers.UUIDField(source='note.uuid', read_only=True)
    job_uuid = serializers.UUIDField(source='job.uuid', read_only=True)

    class Meta:
        model = AIGenerationLog
        fields = (
            'uuid',
            'job_uuid',
            'note_uuid',
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
        read_only_fields = fields
