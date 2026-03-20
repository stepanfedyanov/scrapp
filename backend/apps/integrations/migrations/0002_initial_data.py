from django.db import migrations
import uuid


def create_default_definition(apps, schema_editor):
    IntegrationDefinition = apps.get_model('integrations', 'IntegrationDefinition')
    # create a webhook definition example
    IntegrationDefinition.objects.create(
        id=uuid.uuid4(),
        code='webhook',
        name='Generic Webhook',
        category='automation',
        description='Send POST payload to arbitrary URL',
        config_schema={'type': 'object', 'properties': {'url': {'type': 'string', 'format': 'uri'}}},
        publish_schema=None,
        handler_path='apps.integrations.handlers.webhook.WebhookHandler',
        is_active=True,
        version='1.0',
    )


def delete_default_definition(apps, schema_editor):
    IntegrationDefinition = apps.get_model('integrations', 'IntegrationDefinition')
    IntegrationDefinition.objects.filter(code='webhook').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_definition, delete_default_definition),
    ]
