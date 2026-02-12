from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])


class Blog(SoftDeleteModel):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='blog',
    )
    title = models.CharField(max_length=200, default='My Blog')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.owner_id})"


class Integration(SoftDeleteModel):
    PROVIDERS = [
        ('medium', 'Medium'),
        ('devto', 'Dev.to'),
        ('telegram', 'Telegram'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='integrations',
    )
    name = models.CharField(max_length=120)
    provider = models.CharField(max_length=32, choices=PROVIDERS)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Note(SoftDeleteModel):
    STATUS_DRAFT = 'draft'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_PUBLISHED = 'published'
    STATUS_ARCHIVED = 'archived'
    STATUS_DELETED = 'deleted'

    STATUSES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_PUBLISHED, 'Published'),
        (STATUS_ARCHIVED, 'Archived'),
        (STATUS_DELETED, 'Deleted'),
    ]

    blog = models.ForeignKey(
        Blog,
        on_delete=models.PROTECT,
        related_name='notes',
    )
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default=STATUS_DRAFT,
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.title


class BlogIntegration(SoftDeleteModel):
    blog = models.ForeignKey(
        Blog,
        on_delete=models.PROTECT,
        related_name='blog_integrations',
    )
    integration = models.ForeignKey(
        Integration,
        on_delete=models.PROTECT,
        related_name='blog_integrations',
    )
    enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('blog', 'integration')


class NoteIntegration(SoftDeleteModel):
    note = models.ForeignKey(
        Note,
        on_delete=models.PROTECT,
        related_name='note_integrations',
    )
    integration = models.ForeignKey(
        Integration,
        on_delete=models.PROTECT,
        related_name='note_integrations',
    )
    enabled = models.BooleanField(default=True)
    use_blog_defaults = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('note', 'integration')
