from django.db import migrations


DEFAULT_PROVIDER_DEFINITIONS = [
    {
        'code': 'openai',
        'name': 'OpenAI',
        'handler_path': 'apps.ai_platform.handlers.openai.OpenAIProviderHandler',
        'capabilities': {
            'chat_completion': True,
            'json_output': True,
        },
        'priority': 10,
        'version': '1.0',
    },
    {
        'code': 'anthropic',
        'name': 'Anthropic',
        'handler_path': 'apps.ai_platform.handlers.anthropic.AnthropicProviderHandler',
        'capabilities': {
            'chat_completion': True,
            'json_output': True,
        },
        'priority': 20,
        'version': '1.0',
    },
    {
        'code': 'google',
        'name': 'Google',
        'handler_path': 'apps.ai_platform.handlers.google.GoogleProviderHandler',
        'capabilities': {
            'chat_completion': True,
            'json_output': True,
        },
        'priority': 30,
        'version': '1.0',
    },
]

DEFAULT_MODEL_DEFINITIONS = {
    'openai': [
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
    ],
    'anthropic': [
        {
            'code': 'claude-3-5-sonnet-latest',
            'display_name': 'Claude 3.5 Sonnet',
            'max_context_tokens': 200000,
            'max_output_tokens': 8192,
            'priority': 10,
        }
    ],
    'google': [
        {
            'code': 'gemini-2.0-flash',
            'display_name': 'Gemini 2.0 Flash',
            'max_context_tokens': 1000000,
            'max_output_tokens': 8192,
            'priority': 10,
        }
    ],
}

DEFAULT_PROMPT_TEMPLATES = [
    {
        'code': 'write_structure_default',
        'name': 'Write structure default',
        'operation_type': 'write_structure',
        'system_prompt': 'You are a writing assistant that builds concise article outlines.',
        'user_prompt_template': (
            'Create an outline for a note with title: "{note_title}". '
            'Use h2 and h3 structure.'
        ),
        'version': '1.0',
        'priority': 10,
    },
    {
        'code': 'write_note_default',
        'name': 'Write note default',
        'operation_type': 'write_note',
        'system_prompt': 'You are a writing assistant that generates complete structured notes.',
        'user_prompt_template': (
            'Generate structure and full text for note title: "{note_title}". '
            'Return a coherent article.'
        ),
        'version': '1.0',
        'priority': 10,
    },
    {
        'code': 'write_new_chapter_default',
        'name': 'Write new chapter default',
        'operation_type': 'write_new_chapter',
        'system_prompt': 'You are a writing assistant that expands articles with new chapters.',
        'user_prompt_template': (
            'Given existing headings and context, generate a new chapter (heading + text).'
        ),
        'version': '1.0',
        'priority': 10,
    },
    {
        'code': 'write_more_text_default',
        'name': 'Write more text default',
        'operation_type': 'write_more_text',
        'system_prompt': 'You are a writing assistant that continues current section text.',
        'user_prompt_template': (
            'Continue the text for the current section with consistent style and tone.'
        ),
        'version': '1.0',
        'priority': 10,
    },
]


def seed_initial_data(apps, schema_editor):
    AIProviderDefinition = apps.get_model('ai_platform', 'AIProviderDefinition')
    AIModelDefinition = apps.get_model('ai_platform', 'AIModelDefinition')
    AIPromptTemplate = apps.get_model('ai_platform', 'AIPromptTemplate')
    AIGlobalConfig = apps.get_model('ai_platform', 'AIGlobalConfig')

    provider_by_code = {}
    for provider_data in DEFAULT_PROVIDER_DEFINITIONS:
        provider, _ = AIProviderDefinition.objects.update_or_create(
            code=provider_data['code'],
            defaults={
                'name': provider_data['name'],
                'handler_path': provider_data['handler_path'],
                'capabilities': provider_data.get('capabilities', {}),
                'priority': provider_data.get('priority', 100),
                'is_active': True,
                'version': provider_data.get('version', '1.0'),
            },
        )
        provider_by_code[provider.code] = provider

    for provider_code, model_list in DEFAULT_MODEL_DEFINITIONS.items():
        provider = provider_by_code.get(provider_code)
        if not provider:
            continue

        for model_data in model_list:
            AIModelDefinition.objects.update_or_create(
                provider=provider,
                code=model_data['code'],
                defaults={
                    'display_name': model_data['display_name'],
                    'max_context_tokens': model_data.get('max_context_tokens', 4096),
                    'max_output_tokens': model_data.get('max_output_tokens', 2048),
                    'priority': model_data.get('priority', 100),
                    'is_active': True,
                    'metadata': model_data.get('metadata', {}),
                },
            )

    for prompt_data in DEFAULT_PROMPT_TEMPLATES:
        AIPromptTemplate.objects.update_or_create(
            code=prompt_data['code'],
            defaults={
                'name': prompt_data['name'],
                'operation_type': prompt_data['operation_type'],
                'system_prompt': prompt_data['system_prompt'],
                'user_prompt_template': prompt_data['user_prompt_template'],
                'priority': prompt_data.get('priority', 100),
                'is_active': True,
                'version': prompt_data.get('version', '1.0'),
                'notes': prompt_data.get('notes', ''),
            },
        )

    AIGlobalConfig.objects.update_or_create(
        singleton_id=1,
        defaults={
            'request_timeout_seconds': 60,
            'retry_count': 2,
            'retry_backoff_seconds': 3,
            'max_parallel_tasks': 4,
            'queue_name': 'ai',
            'default_temperature': 0.7,
            'default_max_tokens': 1200,
        },
    )


def rollback_seed_data(apps, schema_editor):
    AIProviderDefinition = apps.get_model('ai_platform', 'AIProviderDefinition')
    AIPromptTemplate = apps.get_model('ai_platform', 'AIPromptTemplate')
    AIGlobalConfig = apps.get_model('ai_platform', 'AIGlobalConfig')

    provider_codes = [item['code'] for item in DEFAULT_PROVIDER_DEFINITIONS]
    prompt_codes = [item['code'] for item in DEFAULT_PROMPT_TEMPLATES]

    AIProviderDefinition.objects.filter(code__in=provider_codes).delete()
    AIPromptTemplate.objects.filter(code__in=prompt_codes).delete()
    AIGlobalConfig.objects.filter(singleton_id=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ai_platform', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_initial_data, rollback_seed_data),
    ]
