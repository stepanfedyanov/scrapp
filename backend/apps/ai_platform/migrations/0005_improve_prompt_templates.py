from django.db import migrations


UPDATED_PROMPTS = [
    {
        'code': 'write_note_default',
        'system_prompt': (
            'You are a writing assistant. '
            'You produce complete articles expressed as a sequence of JSON operations.'
        ),
        'user_prompt_template': (
            'Write a full article for the note titled "{note_title}".\n'
            'Output the article as a sequence of operations:\n'
            '- Use insert_header (level 2) for main section headings.\n'
            '- Use insert_header (level 3) for subsection headings.\n'
            '- Use insert_text with HTML content for every paragraph.\n'
            'Include: an introduction (1-2 paragraphs), at least 3 sections '
            'with headings and body text, and a conclusion.'
        ),
    },
    {
        'code': 'write_structure_default',
        'system_prompt': (
            'You are a writing assistant. '
            'You produce article outlines expressed as a sequence of JSON operations.'
        ),
        'user_prompt_template': (
            'Create a section outline for the note titled "{note_title}".\n'
            'Output only insert_header operations:\n'
            '- level 2 for main sections (4-6 sections).\n'
            '- level 3 for subsections where appropriate.'
        ),
    },
    {
        'code': 'write_new_chapter_default',
        'system_prompt': (
            'You are a writing assistant. '
            'You expand articles by adding new chapters expressed as JSON operations.'
        ),
        'user_prompt_template': (
            'Add a new chapter to the article titled "{note_title}".\n'
            'Output operations in this order:\n'
            '1. One insert_header operation (level 2) for the chapter title.\n'
            '2. Two to four insert_text operations with HTML paragraphs for the chapter body.'
        ),
    },
    {
        'code': 'write_more_text_default',
        'system_prompt': (
            'You are a writing assistant. '
            'You continue article sections by producing additional text as JSON operations.'
        ),
        'user_prompt_template': (
            'Continue the text for the current section of the article "{note_title}".\n'
            'Output two to four insert_text operations with HTML paragraphs. '
            'Match the existing style and tone.'
        ),
    },
]


def update_prompt_templates(apps, schema_editor):
    AIPromptTemplate = apps.get_model('ai_platform', 'AIPromptTemplate')
    for data in UPDATED_PROMPTS:
        AIPromptTemplate.objects.filter(code=data['code']).update(
            system_prompt=data['system_prompt'],
            user_prompt_template=data['user_prompt_template'],
        )


def revert_prompt_templates(apps, schema_editor):
    AIPromptTemplate = apps.get_model('ai_platform', 'AIPromptTemplate')
    ORIGINAL = {
        'write_note_default': {
            'system_prompt': 'You are a writing assistant that generates complete structured notes.',
            'user_prompt_template': (
                'Generate structure and full text for note title: "{note_title}". '
                'Return a coherent article.'
            ),
        },
        'write_structure_default': {
            'system_prompt': 'You are a writing assistant that builds concise article outlines.',
            'user_prompt_template': (
                'Create an outline for a note with title: "{note_title}". '
                'Use h2 and h3 structure.'
            ),
        },
        'write_new_chapter_default': {
            'system_prompt': 'You are a writing assistant that expands articles with new chapters.',
            'user_prompt_template': (
                'Given existing headings and context, generate a new chapter (heading + text).'
            ),
        },
        'write_more_text_default': {
            'system_prompt': 'You are a writing assistant that continues current section text.',
            'user_prompt_template': (
                'Continue the text for the current section with consistent style and tone.'
            ),
        },
    }
    for code, data in ORIGINAL.items():
        AIPromptTemplate.objects.filter(code=code).update(**data)


class Migration(migrations.Migration):
    dependencies = [
        ('ai_platform', '0004_refresh_openai_models_54'),
    ]

    operations = [
        migrations.RunPython(
            update_prompt_templates,
            revert_prompt_templates,
        ),
    ]
