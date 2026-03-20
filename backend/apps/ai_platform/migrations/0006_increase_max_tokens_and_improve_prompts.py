from django.db import migrations


EXAMPLE_OPERATIONS = (
    '{"operations": ['
    '{"type":"insert_text","html":"<p>Introduction paragraph.</p>"},'
    '{"type":"insert_header","level":2,"text":"Section Title"},'
    '{"type":"insert_text","html":"<p>Section body paragraph.</p>"}'
    ']}'
)

UPDATED_PROMPTS = [
    {
        'code': 'write_note_default',
        'system_prompt': (
            'You are a writing assistant. '
            'Your only output is a JSON object containing an "operations" array. '
            'Every piece of content you write must appear as an operation inside that array. '
            'Example of a valid response:\n'
            + EXAMPLE_OPERATIONS
        ),
        'user_prompt_template': (
            'Write a complete article for the note titled "{note_title}".\n\n'
            'Structure the article as follows:\n'
            '1. An introduction: 1-2 insert_text operations.\n'
            '2. At least 3 main sections, each starting with an insert_header (level 2) '
            'followed by 2-3 insert_text operations.\n'
            '3. A conclusion: 1 insert_text operation.\n\n'
            'Rules:\n'
            '- Use insert_header level 3 for subsections if needed.\n'
            '- Each insert_text must have an "html" field with valid HTML (use <p> tags).\n'
            '- Output ONLY the JSON object, no extra text.'
        ),
    },
    {
        'code': 'write_structure_default',
        'system_prompt': (
            'You are a writing assistant. '
            'Your only output is a JSON object containing an "operations" array of insert_header items. '
            'Example of a valid response:\n'
            '{"operations":['
            '{"type":"insert_header","level":2,"text":"First Section"},'
            '{"type":"insert_header","level":3,"text":"A Subsection"},'
            '{"type":"insert_header","level":2,"text":"Second Section"}'
            ']}'
        ),
        'user_prompt_template': (
            'Create a section outline for the note titled "{note_title}".\n\n'
            '- Use 4-6 insert_header operations at level 2 for main sections.\n'
            '- Add level 3 headers for subsections where appropriate.\n'
            '- Output ONLY the JSON object, no extra text.'
        ),
    },
    {
        'code': 'write_new_chapter_default',
        'system_prompt': (
            'You are a writing assistant. '
            'Your only output is a JSON object containing an "operations" array. '
            'Example of a valid response:\n'
            '{"operations":['
            '{"type":"insert_header","level":2,"text":"New Chapter"},'
            '{"type":"insert_text","html":"<p>First paragraph of the chapter.</p>"},'
            '{"type":"insert_text","html":"<p>Second paragraph.</p>"}'
            ']}'
        ),
        'user_prompt_template': (
            'Add a new chapter to the article titled "{note_title}".\n\n'
            '- Start with exactly one insert_header (level 2) for the chapter title.\n'
            '- Follow with 2-4 insert_text operations with HTML paragraphs.\n'
            '- Output ONLY the JSON object, no extra text.'
        ),
    },
    {
        'code': 'write_more_text_default',
        'system_prompt': (
            'You are a writing assistant. '
            'Your only output is a JSON object containing an "operations" array of insert_text items. '
            'Example of a valid response:\n'
            '{"operations":['
            '{"type":"insert_text","html":"<p>Continuation paragraph one.</p>"},'
            '{"type":"insert_text","html":"<p>Continuation paragraph two.</p>"}'
            ']}'
        ),
        'user_prompt_template': (
            'Continue the current section of the article "{note_title}".\n\n'
            '- Output 2-4 insert_text operations with HTML paragraphs.\n'
            '- Match the existing style and tone.\n'
            '- Output ONLY the JSON object, no extra text.'
        ),
    },
]


def apply_changes(apps, schema_editor):
    AIGlobalConfig = apps.get_model('ai_platform', 'AIGlobalConfig')
    AIPromptTemplate = apps.get_model('ai_platform', 'AIPromptTemplate')

    AIGlobalConfig.objects.filter(singleton_id=1).update(default_max_tokens=4096)

    for data in UPDATED_PROMPTS:
        AIPromptTemplate.objects.filter(code=data['code']).update(
            system_prompt=data['system_prompt'],
            user_prompt_template=data['user_prompt_template'],
        )


def revert_changes(apps, schema_editor):
    AIGlobalConfig = apps.get_model('ai_platform', 'AIGlobalConfig')
    AIGlobalConfig.objects.filter(singleton_id=1).update(default_max_tokens=1200)


class Migration(migrations.Migration):
    dependencies = [
        ('ai_platform', '0005_improve_prompt_templates'),
    ]

    operations = [
        migrations.RunPython(apply_changes, revert_changes),
    ]
