from django.contrib import admin

from .models import Blog, Note, Integration, BlogIntegration, NoteIntegration


admin.site.register(Blog)
admin.site.register(Note)
admin.site.register(Integration)
admin.site.register(BlogIntegration)
admin.site.register(NoteIntegration)
