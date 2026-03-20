import logging
from django.utils.module_loading import import_string
from typing import Any, Dict, Type

logger = logging.getLogger(__name__)

_registry: Dict[str, Type[Any]] = { }


def register(code: str, handler_cls: Type[Any]) -> None:
    """Register a handler class under a given integration code."""
    if code in _registry:
        logger.warning("overwriting handler for code %s", code)
    _registry[code] = handler_cls


def get_handler(code: str) -> Any:
    """Return an instance of handler for the given code.

    The handler_path is resolved only once and cached.
    """
    handler_cls = _registry.get(code)
    if handler_cls is not None:
        return handler_cls()

    # dynamic import using handler_path from definition
    from .models import IntegrationDefinition

    try:
        definition = IntegrationDefinition.objects.get(code=code)
    except IntegrationDefinition.DoesNotExist:
        raise LookupError(f"no integration definition with code {code}")

    path = definition.handler_path
    try:
        cls = import_string(path)
    except ImportError as exc:
        logger.error("failed to import handler %s: %s", path, exc)
        raise

    register(code, cls)
    return cls()


class BaseIntegrationHandler:
    def publish(self, integration, publish_target, content: dict):
        """Perform the actual publish operation.

        Must be implemented by subclasses.
        """
        raise NotImplementedError
