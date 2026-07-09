"""
Event service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Event domain.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
import logging

logger = logging.getLogger(__name__)


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
            data: Dictionary containing event data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            str: The ID of the created event document
        """
        try:
            EventService._check_permission(token, "create")

            if "_id" in data:
                del data["_id"]

            data["created"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            event_id = mongo.create_document(config.EVENT_COLLECTION_NAME, data)
            logger.info(f"Created event { event_id} for user {token.get('user_id')}")
            return event_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating event: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create event: {error_msg}")

    @staticmethod
    def get_event(event_id, token, breadcrumb):
        """
        Retrieve a specific event document by ID.

        Used internally after create to return the created document.
        """
        try:
            EventService._check_permission(token, "read")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            event = mongo.get_document(config.EVENT_COLLECTION_NAME, event_id)
            if event is None:
                raise HTTPNotFound(f"Event { event_id} not found")

            logger.info(f"Retrieved event { event_id} for user {token.get('user_id')}")
            return event
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving event { event_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve event { event_id}")
