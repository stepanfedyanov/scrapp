from django.core.exceptions import ObjectDoesNotExist

from apps.ai_platform.models import (
    AIGlobalConfig,
    AIModelDefinition,
    AIPromptTemplate,
    AIProviderCredential,
)


class RuntimeResolutionError(Exception):
    pass


def resolve_runtime(operation_type: str, model_code: str | None = None):
    try:
        config = AIGlobalConfig.objects.get(
            singleton_id=AIGlobalConfig.SINGLETON_ID
        )
    except ObjectDoesNotExist as exc:
        raise RuntimeResolutionError(
            'AI global config is not configured.'
        ) from exc

    prompt = (
        AIPromptTemplate.objects
        .filter(operation_type=operation_type, is_active=True)
        .order_by('priority', 'name')
        .first()
    )
    if prompt is None:
        raise RuntimeResolutionError(
            'No active prompt template configured for operation: '
            f'{operation_type}'
        )

    model_queryset = AIModelDefinition.objects.filter(
        is_active=True,
        provider__is_active=True,
    )
    if model_code:
        model = (
            model_queryset.filter(code=model_code)
            .select_related('provider')
            .first()
        )
    else:
        model = (
            model_queryset
            .select_related('provider')
            .order_by('provider__priority', 'priority')
            .first()
        )

    if model is None:
        raise RuntimeResolutionError('No active AI model is configured.')

    requires_credentials = model.provider.capabilities.get(
        'requires_credentials',
        True,
    )
    credential = (
        AIProviderCredential.objects
        .filter(provider=model.provider, is_active=True)
        .first()
    )
    if requires_credentials and credential is None:
        raise RuntimeResolutionError(
            'No active credential configured for provider: '
            f'{model.provider.code}'
        )

    return {
        'global_config': config,
        'prompt_template': prompt,
        'model': model,
        'provider': model.provider,
        'credential': credential,
    }
