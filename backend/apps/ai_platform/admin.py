from django import forms
from django.contrib import admin

from .models import (
    AIGlobalConfig,
    AIModelDefinition,
    AIPromptTemplate,
    AIProviderCredential,
    AIProviderDefinition,
)
from .security import encrypt_secret


class AIProviderCredentialAdminForm(forms.ModelForm):
    api_key_encrypted = forms.CharField(
        label='API key',
        required=False,
        widget=forms.PasswordInput(render_value=False),
    )

    class Meta:
        model = AIProviderCredential
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['api_key_encrypted'].help_text = (
                'Leave blank to keep the existing key. '
                f'Current: {self.instance.api_key_masked or "not set"}'
            )
        else:
            self.fields['api_key_encrypted'].help_text = (
                'Enter provider API key. It will be encrypted before save.'
            )

    def clean_api_key_encrypted(self):
        value = (self.cleaned_data.get('api_key_encrypted') or '').strip()

        if not value and self.instance and self.instance.pk:
            return self.instance.api_key_encrypted

        if not value:
            return ''

        return encrypt_secret(value)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


@admin.register(AIProviderDefinition)
class AIProviderDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'is_active',
        'priority',
        'version',
        'updated_at',
    )
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(AIModelDefinition)
class AIModelDefinitionAdmin(admin.ModelAdmin):
    list_display = (
        'provider',
        'code',
        'display_name',
        'max_context_tokens',
        'max_output_tokens',
        'is_active',
    )
    list_filter = ('provider', 'is_active')
    search_fields = ('provider__code', 'code', 'display_name')


@admin.register(AIProviderCredential)
class AIProviderCredentialAdmin(admin.ModelAdmin):
    form = AIProviderCredentialAdminForm
    list_display = ('provider', 'is_active', 'api_key_preview', 'updated_at')
    list_filter = ('is_active', 'provider')
    search_fields = ('provider__code', 'provider__name')
    readonly_fields = (
        'api_key_preview',
        'last_validated_at',
        'created_at',
        'updated_at',
    )

    @admin.display(description='API key')
    def api_key_preview(self, obj):
        return obj.api_key_masked or 'not set'


@admin.register(AIGlobalConfig)
class AIGlobalConfigAdmin(admin.ModelAdmin):
    list_display = (
        'request_timeout_seconds',
        'retry_count',
        'retry_backoff_seconds',
        'max_parallel_tasks',
        'queue_name',
        'updated_at',
    )

    def has_add_permission(self, request):
        if AIGlobalConfig.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(AIPromptTemplate)
class AIPromptTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'operation_type',
        'is_active',
        'priority',
        'version',
    )
    list_filter = ('operation_type', 'is_active')
    search_fields = ('code', 'name')
