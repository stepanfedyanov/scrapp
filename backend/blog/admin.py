from django.contrib import admin

from .models import Blog, Note, Integration, BlogIntegration, NoteIntegration


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'blog', 'status', 'created_at')


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ('title', 'name', 'provider', 'status', 'definition', 'owner')
    list_filter = ('status',)


admin.site.register(BlogIntegration)
admin.site.register(NoteIntegration)
