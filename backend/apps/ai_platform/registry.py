from django.utils.module_loading import import_string

from .models import AIProviderDefinition


class BaseAIProviderHandler:
    def generate(self, *, model_code, prompt, options, credentials, context):
        raise NotImplementedError


_handler_cache = {}


def get_provider_handler(provider_code: str):
    if provider_code in _handler_cache:
        return _handler_cache[provider_code]

    provider = AIProviderDefinition.objects.get(code=provider_code, is_active=True)
    handler_cls = import_string(provider.handler_path)
    handler = handler_cls()
    _handler_cache[provider_code] = handler
    return handler
