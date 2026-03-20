from apps.ai_platform.registry import BaseAIProviderHandler


def _render_user_prompt(prompt, context):
    return (prompt.get('template') or '').format_map(context)


class OpenAIProviderHandler(BaseAIProviderHandler):
    def generate(self, *, model_code, prompt, options, credentials, context):
        import json

        from openai import OpenAI

        client = OpenAI(
            api_key=credentials.get('api_key') or None,
            base_url=credentials.get('base_url') or None,
            organization=credentials.get('organization') or None,
        )
        completion = client.chat.completions.create(
            model=model_code,
            response_format={'type': 'json_object'},
            temperature=options.get('temperature'),
            max_completion_tokens=options.get('max_tokens'),
            messages=[
                {
                    'role': 'system',
                    'content': prompt.get('system', '').strip(),
                },
                {
                    'role': 'user',
                    'content': _render_user_prompt(prompt, context),
                },
            ],
        )
        choice = completion.choices[0]
        content = choice.message.content
        if not content:
            raise ValueError(
                f'OpenAI returned empty content. '
                f'finish_reason={choice.finish_reason!r}, '
                f'model={model_code!r}'
            )
        return json.loads(content)
