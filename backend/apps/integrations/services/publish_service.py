import logging
from typing import Dict, Any

from django.utils import timezone

from apps.integrations import registry
from apps.integrations.models import PublishLog, PublishTarget

logger = logging.getLogger(__name__)


def publish_target(publish_target: PublishTarget, content: Dict[str, Any]) -> None:
    """Attempt to publish a target using its integration handler.

    Updates target status, retry counters and logs the attempt.
    """
    if not publish_target.is_enabled:
        logger.debug("publish target %s is disabled, skipping", publish_target.pk)
        return

    if publish_target.status == PublishTarget.STATUS_PUBLISHED:
        logger.debug("publish target %s already published, skipping", publish_target.pk)
        return

    code = publish_target.integration.definition.code
    try:
        handler = registry.get_handler(code)
    except Exception as exc:
        logger.exception("could not load handler for %s", code)
        publish_target.retry_count += 1
        publish_target.status = PublishTarget.STATUS_FAILED
        publish_target.last_error = str(exc)
        publish_target.save(update_fields=['retry_count', 'status', 'last_error'])
        # record log even when handler can't be loaded
        PublishLog.objects.create(
            publish_target=publish_target,
            request_payload=content,
            response_payload=None,
            status=PublishLog.STATUS_ERROR,
            error_message=str(exc),
        )
        return

    log_kwargs: Dict[str, Any] = {
        'publish_target': publish_target,
        'request_payload': content,
        'response_payload': None,
        'status': None,
        'error_message': '',
    }

    try:
        result = handler.publish(publish_target.integration, publish_target, content)
        # handler may return response payload
        log_kwargs['response_payload'] = result
        publish_target.status = PublishTarget.STATUS_PUBLISHED
        publish_target.last_published_at = timezone.now()
        publish_target.retry_count = 0
        publish_target.last_error = ''
    except Exception as exc:
        logger.exception("error publishing target %s", publish_target.pk)
        publish_target.retry_count += 1
        publish_target.status = PublishTarget.STATUS_FAILED
        publish_target.last_error = str(exc)
        log_kwargs['error_message'] = str(exc)
        log_kwargs['status'] = PublishLog.STATUS_ERROR
    else:
        log_kwargs['status'] = PublishLog.STATUS_SUCCESS
    finally:
        publish_target.save()
        PublishLog.objects.create(**log_kwargs)
