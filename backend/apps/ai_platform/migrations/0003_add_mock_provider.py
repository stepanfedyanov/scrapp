from django.db import migrations


def add_mock_provider(apps, schema_editor):
    AIProviderDefinition = apps.get_model('ai_platform', 'AIProviderDefinition')
    AIModelDefinition = apps.get_model('ai_platform', 'AIModelDefinition')

    provider, _ = AIProviderDefinition.objects.update_or_create(
        code='mock',
        defaults={
            'name': 'Mock Provider',
            'handler_path': 'apps.ai_platform.handlers.mock.MockProviderHandler',
            'capabilities': {
                'chat_completion': True,
                'json_output': True,
                'requires_credentials': False,
            },
            'priority': 1,
            'is_active': True,
            'version': '1.0',
        },
    )

    AIModelDefinition.objects.update_or_create(
        provider=provider,
        code='mock-v1',
        defaults={
            'display_name': 'Mock model',
            'max_context_tokens': 32000,
            'max_output_tokens': 4096,
            'priority': 1,
            'is_active': True,
            'metadata': {},
        },
    )


def remove_mock_provider(apps, schema_editor):
    AIProviderDefinition = apps.get_model('ai_platform', 'AIProviderDefinition')
    AIProviderDefinition.objects.filter(code='mock').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ai_platform', '0002_initial_data'),
    ]

    operations = [
        migrations.RunPython(add_mock_provider, remove_mock_provider),
    ]
