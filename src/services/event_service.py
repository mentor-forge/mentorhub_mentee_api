"""
Event service for business logic and RBAC.

Subclasses shared EventService and triggers AggregationService.add_hit on link events.
"""

import logging
from api_utils import Config
from api_utils.services import EventService as SharedEventService

logger = logging.getLogger(__name__)


class EventService(SharedEventService):
    """Mentee Event service: triggers aggregation hit on link event creation."""

    @classmethod
    def create_event(cls, data, token, breadcrumb):
        """
        Create event document and trigger aggregation hit if type is link and token has resource_id.
        """
        created = super().create_event(data, token, breadcrumb)
        config = Config.get_instance()
        link_type = getattr(config, "EVENT_TYPE_LINK", "link")
        if created.get("type") == link_type:
            resource_id = token.get("resource_id")
            if resource_id:
                from src.services.aggregation_service import AggregationService

                AggregationService.add_hit(resource_id, token, breadcrumb)
            else:
                logger.warning(
                    "link event created without resource_id in token; skipping add_hit"
                )
        return created
