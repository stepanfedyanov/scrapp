from django.db import migrations


OPENAI_MODELS_54 = [
    {
        'code': 'gpt-5.4',
        'display_name': 'GPT-5.4',
        'max_context_tokens': 128000,
        'max_output_tokens': 16384,
        'priority': 10,
    },
    {
        'code': 'gpt-5.4-pro',
        'display_name': 'GPT-5.4 Pro',
        'max_context_tokens': 128000,
        'max_output_tokens': 16384,
        'priority': 20,
    },
    {
        'code': 'gpt-5-mini',
        'display_name': 'GPT-5 mini',
        'max_context_tokens': 128000,
        'max_output_tokens': 16384,
        'priority': 30,
    },
]

LEGACY_OPENAI_MODEL_CODES = [
    'gpt-4o-mini',
    'gpt-4.1-mini',
]


def _set_openai_models(apps, *, models_to_enable, models_to_disable):
    AIProviderDefinition = apps.get_model(
        'ai_platform',
        'AIProviderDefinition',
    )
    AIModelDefinition = apps.get_model('ai_platform', 'AIModelDefinition')

    provider = AIProviderDefinition.objects.filter(code='openai').first()
    if provider is None:
        return

    for model_data in models_to_enable:
        AIModelDefinition.objects.update_or_create(
            provider=provider,
            code=model_data['code'],
            defaults={
                'display_name': model_data['display_name'],
                'max_context_tokens': model_data['max_context_tokens'],
                'max_output_tokens': model_data['max_output_tokens'],
                'priority': model_data['priority'],
                'is_active': True,
            },
        )

    AIModelDefinition.objects.filter(
        provider=provider,
        code__in=models_to_disable,
    ).update(is_active=False)


def forward_refresh_openai_models(apps, schema_editor):
    _set_openai_models(
        apps,
        models_to_enable=OPENAI_MODELS_54,
        models_to_disable=LEGACY_OPENAI_MODEL_CODES,
    )


def backward_refresh_openai_models(apps, schema_editor):
    _set_openai_models(
        apps,
        models_to_enable=[
            {
                'code': 'gpt-4o-mini',
                'display_name': 'GPT-4o mini',
                'max_context_tokens': 128000,
                'max_output_tokens': 16384,
                'priority': 10,
            },
            {
                'code': 'gpt-4.1-mini',
                'display_name': 'GPT-4.1 mini',
                'max_context_tokens': 1047576,
                'max_output_tokens': 32768,
                'priority': 20,
            },
        ],
        models_to_disable=[item['code'] for item in OPENAI_MODELS_54],
    )


class Migration(migrations.Migration):

    dependencies = [
        ('ai_platform', '0003_add_mock_provider'),
    ]

    operations = [
        migrations.RunPython(
            forward_refresh_openai_models,
            backward_refresh_openai_models,
        ),
    ]
