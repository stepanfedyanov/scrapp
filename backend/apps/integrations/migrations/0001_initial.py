from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('blog', '0005_deduplicate_block_uuids'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='IntegrationDefinition',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(db_index=True, max_length=100, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('category', models.CharField(db_index=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('config_schema', models.JSONField()),
                ('publish_schema', models.JSONField(blank=True, null=True)),
                ('handler_path', models.CharField(max_length=500)),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('version', models.CharField(default='1.0', max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
                'indexes': [
                    models.Index(fields=['code'], name='integrat_code_idx'),
                    models.Index(fields=['category'], name='integrat_cat_idx'),
                    models.Index(fields=['is_active'], name='integrat_active_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='PublishTarget',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('publish_settings', models.JSONField(default=dict, blank=True)),
                ('is_enabled', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('queued', 'Queued'), ('published', 'Published'), ('failed', 'Failed')], db_index=True, default='draft', max_length=20)),
                ('scheduled_at', models.DateTimeField(blank=True, null=True)),
                ('last_published_at', models.DateTimeField(blank=True, null=True)),
                ('retry_count', models.IntegerField(default=0)),
                ('last_error', models.TextField(blank=True, null=True)),
                ('object_id', models.UUIDField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(on_delete=models.CASCADE, to='contenttypes.ContentType', db_index=True)),
                ('integration', models.ForeignKey(on_delete=models.CASCADE, related_name='publish_targets', to='blog.integration')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['content_type', 'object_id'], name='ptarget_ct_obj_idx'),
                    models.Index(fields=['status'], name='ptarget_status_idx'),
                    models.Index(fields=['integration'], name='ptarget_integ_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='PublishLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('request_payload', models.JSONField()),
                ('response_payload', models.JSONField(blank=True, null=True)),
                ('status', models.CharField(choices=[('success', 'Success'), ('error', 'Error')], max_length=20)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('publish_target', models.ForeignKey(on_delete=models.CASCADE, related_name='logs', to='integrations.publishtarget')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['publish_target', 'created_at'], name='pl_target_date_idx'),
                ],
            },
        ),
    ]
