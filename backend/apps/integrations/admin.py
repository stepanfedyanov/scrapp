from django.contrib import admin

from .models import IntegrationDefinition, PublishTarget, PublishLog


@admin.register(IntegrationDefinition)
class IntegrationDefinitionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'is_active', 'version', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('code', 'name')


@admin.register(PublishTarget)
class PublishTargetAdmin(admin.ModelAdmin):
    list_display = ('integration', 'content_type', 'object_id', 'status', 'is_enabled', 'scheduled_at')
    list_filter = ('status', 'is_enabled')
    search_fields = ('integration__name',)


@admin.register(PublishLog)
class PublishLogAdmin(admin.ModelAdmin):
    list_display = ('publish_target', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('publish_target__integration__name',)
