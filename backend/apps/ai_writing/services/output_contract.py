OUTPUT_FORMAT_CONTRACT = (
    'Output contract (mandatory):\n'
    'Return ONLY one valid JSON object with this exact top-level structure:\n'
    '{"operations": [...]}\n'
    'Allowed operation types:\n'
    '1) insert_header: {"type":"insert_header","level":2|3,"text":"..."}\n'
    '2) insert_text: {"type":"insert_text","html":"<p>...</p>"}\n'
    'Rules:\n'
    '- No markdown fences.\n'
    '- No explanations, comments, or extra keys outside the JSON object.\n'
    '- Use "html" for text blocks (valid HTML string).\n'
    '- Use only level 2 or 3 for headers.\n'
    '- You MUST include at least one operation — an empty operations array is not acceptable.\n'
)


def apply_output_contract(system_prompt: str) -> str:
    system_prompt = (system_prompt or '').strip()
    if not system_prompt:
        return OUTPUT_FORMAT_CONTRACT

    if OUTPUT_FORMAT_CONTRACT in system_prompt:
        return system_prompt

    return f'{system_prompt}\n\n{OUTPUT_FORMAT_CONTRACT}'
