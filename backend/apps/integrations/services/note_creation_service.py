"""Service for handling post-creation logic with integration defaults.

When a Note is created, automatically create PublishTargets from blog defaults.
"""
import logging
from typing import List

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from blog.models import BlogIntegrationDefault, Note
from apps.integrations.models import PublishTarget

logger = logging.getLogger(__name__)


def create_publish_targets_from_defaults(note: Note) -> List[PublishTarget]:
    """Auto-create PublishTargets from blog default integrations.
    
    Args:
        note: The newly created Note instance
        
    Returns:
        List of created PublishTarget instances
        
    Raises:
        Exception: If transaction fails
    """
    blog = note.blog
    created_targets: List[PublishTarget] = []
    
    try:
        with transaction.atomic():
            # Fetch all active defaults for the blog
            defaults = BlogIntegrationDefault.objects.filter(
                blog=blog,
                is_enabled=True,
            ).select_related('integration')
            
            logger.debug(f"Creating publish targets for note {note.id} from {defaults.count()} defaults")
            
            # Determine content type for Note model
            content_type = ContentType.objects.get_for_model(Note)
            
            # Create PublishTarget for each default
            for default in defaults:
                # Check if target already exists (avoid duplicates)
                existing = PublishTarget.objects.filter(
                    content_type=content_type,
                    object_id=note.uuid,
                    integration=default.integration,
                ).exists()
                
                if existing:
                    logger.debug(
                        f"PublishTarget already exists for note {note.id} "
                        f"and integration {default.integration.id}, skipping"
                    )
                    continue
                
                # Create the target
                target = PublishTarget.objects.create(
                    integration=default.integration,
                    publish_settings=default.publish_settings.copy(),
                    is_enabled=default.is_enabled,
                    status=PublishTarget.STATUS_DRAFT,
                    content_type=content_type,
                    object_id=note.uuid,
                )
                created_targets.append(target)
                logger.debug(f"Created PublishTarget {target.id} for note {note.id}")
            
            return created_targets
            
    except Exception as exc:
        logger.exception(f"Failed to create publish targets for note {note.id}: {exc}")
        raise
