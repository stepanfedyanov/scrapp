from apps.ai_platform.registry import BaseAIProviderHandler


class GoogleProviderHandler(BaseAIProviderHandler):
    def generate(self, *, model_code, prompt, options, credentials, context):
        import json

        import google.generativeai as genai

        genai.configure(api_key=credentials.get('api_key') or None)
        model = genai.GenerativeModel(
            model_name=model_code,
            system_instruction=(
                f"{prompt.get('system', '').strip()}\n\n"
                'Return only JSON with an "operations" array. '
                'Each item must use type "insert_header" or "insert_text".'
            ).strip(),
        )
        response = model.generate_content(
            (prompt.get('template') or '').format_map(context),
            generation_config={
                'temperature': options.get('temperature'),
                'max_output_tokens': options.get('max_tokens'),
                'response_mime_type': 'application/json',
            },
        )
        return json.loads(response.text or '{"operations": []}')
