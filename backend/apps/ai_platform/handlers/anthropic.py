from apps.ai_platform.registry import BaseAIProviderHandler


def _extract_json_block(text):
    stripped = text.strip()
    if stripped.startswith('{'):
        return stripped

    marker = '```json'
    start = stripped.find(marker)
    if start == -1:
        start = stripped.find('```')
        if start == -1:
            return stripped
        start += 3
    else:
        start += len(marker)

    end = stripped.find('```', start)
    if end == -1:
        return stripped[start:].strip()
    return stripped[start:end].strip()


class AnthropicProviderHandler(BaseAIProviderHandler):
    def generate(self, *, model_code, prompt, options, credentials, context):
        import importlib
        import json

        anthropic = importlib.import_module('anthropic')
        client = anthropic.Anthropic(
            api_key=credentials.get('api_key') or None,
            base_url=credentials.get('base_url') or None,
        )
        message = client.messages.create(
            model=model_code,
            max_tokens=options.get('max_tokens') or 2048,
            temperature=options.get('temperature'),
            system=(
                f"{prompt.get('system', '').strip()}\n\n"
                'Return only JSON with an "operations" array. '
                'Each item must use type "insert_header" or "insert_text".'
            ).strip(),
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': (
                                prompt.get('template') or ''
                            ).format_map(context),
                        }
                    ],
                }
            ],
        )
        text_response = ''.join(
            block.text
            for block in message.content
            if getattr(block, 'type', '') == 'text'
        )
        return json.loads(_extract_json_block(text_response))
