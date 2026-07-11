"""
Event service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Event domain.
"""

from bson import ObjectId

from api_utils import MongoIO, Config
from api_utils.mongo_utils import encode_document
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPInternalServerError,
)
import logging

logger = logging.getLogger(__name__)

ID_PROPERTIES = ["_id", "profile_id", "resource_id", "journey_id"]
DATE_PROPERTIES = []


class EventService:
    """
    Service class for Event domain operations.
    """

    @staticmethod
    def _check_permission(token, operation):
        """Any authenticated user may create events."""
        pass

    @staticmethod
    def create_event(data, token, breadcrumb):
        """
        Create a new event document.

        Args:
            data: Dictionary containing event data (type only from client)
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: The created event document including _id
        """
        try:
            EventService._check_permission(token, "create")

            if "_id" in data:
                del data["_id"]
            data.pop("context", None)
            data.pop("created", None)

            data["context"] = dict(token)

            encode_document(data, ID_PROPERTIES, DATE_PROPERTIES)

            data["created"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            event_id = mongo.create_document(config.EVENT_COLLECTION_NAME, data)
            if "_id" not in data:
                data["_id"] = ObjectId(event_id)
            logger.info(f"Created event {event_id} for user {token.get('user_id')}")

            if data.get("type") == "link":
                resource_id = token.get("resource_id")
                if resource_id:
                    from src.services.aggregation_service import AggregationService

                    AggregationService.add_hit(resource_id, token, breadcrumb)
                else:
                    logger.warning(
                        "link event created without resource_id in token; skipping add_hit"
                    )

            return data
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating event: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create event: {error_msg}")
