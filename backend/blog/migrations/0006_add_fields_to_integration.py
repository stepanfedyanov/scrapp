from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_deduplicate_block_uuids'),
        ('integrations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='integration',
            name='definition',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='integrations',
                to='integrations.integrationdefinition',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='integration',
            name='title',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='integration',
            name='credentials',
            field=models.JSONField(default=dict, blank=True),
        ),
        migrations.AddField(
            model_name='integration',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('disabled', 'Disabled'), ('error', 'Error')], default='active', max_length=20, db_index=True),
        ),
        migrations.AddField(
            model_name='integration',
            name='last_error',
            field=models.TextField(blank=True, null=True),
        ),
    ]
