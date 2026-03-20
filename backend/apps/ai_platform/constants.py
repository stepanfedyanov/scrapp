OPERATION_WRITE_STRUCTURE = 'write_structure'
OPERATION_WRITE_NOTE = 'write_note'
OPERATION_WRITE_NEW_CHAPTER = 'write_new_chapter'
OPERATION_WRITE_MORE_TEXT = 'write_more_text'

OPERATION_CHOICES = [
    (OPERATION_WRITE_STRUCTURE, 'Write structure'),
    (OPERATION_WRITE_NOTE, 'Write note'),
    (OPERATION_WRITE_NEW_CHAPTER, 'Write new chapter'),
    (OPERATION_WRITE_MORE_TEXT, 'Write more text'),
]

PROVIDER_MOCK = 'mock'
PROVIDER_OPENAI = 'openai'
PROVIDER_ANTHROPIC = 'anthropic'
PROVIDER_GOOGLE = 'google'

DEFAULT_PROVIDER_DEFINITIONS = [
    {
        'code': PROVIDER_MOCK,
        'name': 'Mock Provider',
        'handler_path': 'apps.ai_platform.handlers.mock.MockProviderHandler',
        'capabilities': {
            'chat_completion': True,
            'json_output': True,
            'requires_credentials': False,
        },
        'priority': 1,
        'version': '1.0',
    },
    {
        'code': PROVIDER_OPENAI,
        'name': 'OpenAI',
        'handler_path': (
            'apps.ai_platform.handlers.openai.OpenAIProviderHandler'
        ),
        'capabilities': {
            'chat_completion': True,
            'json_output': True,
        },
        'priority': 10,
        'version': '1.0',
    },
    {
        'code': PROVIDER_ANTHROPIC,
        'name': 'Anthropic',
        'handler_path': (
            'apps.ai_platform.handlers.anthropic.AnthropicProviderHandler'
        ),
        'capabilities': {
            'chat_completion': True,
            'json_output': True,
        },
        'priority': 20,
        'version': '1.0',
    },
    {
        'code': PROVIDER_GOOGLE,
        'name': 'Google',
        'handler_path': (
            'apps.ai_platform.handlers.google.GoogleProviderHandler'
        ),
        'capabilities': {
            'chat_completion': True,
            'json_output': True,
        },
        'priority': 30,
        'version': '1.0',
    },
]

DEFAULT_MODEL_DEFINITIONS = {
    PROVIDER_MOCK: [
        {
            'code': 'mock-v1',
            'display_name': 'Mock model',
            'max_context_tokens': 32000,
            'max_output_tokens': 4096,
            'priority': 1,
        }
    ],
    PROVIDER_OPENAI: [
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
    PROVIDER_ANTHROPIC: [
        {
            'code': 'claude-3-5-sonnet-latest',
            'display_name': 'Claude 3.5 Sonnet',
            'max_context_tokens': 200000,
            'max_output_tokens': 8192,
            'priority': 10,
        }
    ],
    PROVIDER_GOOGLE: [
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
        'operation_type': OPERATION_WRITE_STRUCTURE,
        'system_prompt': (
            'You are a writing assistant that builds concise article outlines.'
        ),
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
        'operation_type': OPERATION_WRITE_NOTE,
        'system_prompt': (
            'You are a writing assistant that generates '
            'complete structured notes.'
        ),
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
        'operation_type': OPERATION_WRITE_NEW_CHAPTER,
        'system_prompt': (
            'You are a writing assistant that expands '
            'articles with new chapters.'
        ),
        'user_prompt_template': (
            'Given existing headings and context, generate a new chapter '
            '(heading + text).'
        ),
        'version': '1.0',
        'priority': 10,
    },
    {
        'code': 'write_more_text_default',
        'name': 'Write more text default',
        'operation_type': OPERATION_WRITE_MORE_TEXT,
        'system_prompt': (
            'You are a writing assistant that continues current section text.'
        ),
        'user_prompt_template': (
            'Continue the text for the current section with consistent style '
            'and tone.'
        ),
        'version': '1.0',
        'priority': 10,
    },
]
