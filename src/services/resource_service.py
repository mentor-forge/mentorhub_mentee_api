"""
Resource service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Resource domain.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
import logging

logger = logging.getLogger(__name__)

DEFAULT_OFFSET = 0
DEFAULT_SIZE = 20
MAX_SIZE = 100
ARCHIVED_STATUS = "archived"


class ResourceService:
    """
    Service class for Resource domain operations.

    Handles:
    - RBAC authorization checks (placeholder for future implementation)
    - MongoDB operations via MongoIO singleton
    - Business logic for Resource domain (read-only)
    """

    @staticmethod
    def _check_permission(token, operation):
        """
        Check if the user has permission to perform an operation.

        Args:
            token: Token dictionary with user_id and roles
            operation: The operation being performed (e.g., 'read')

        Raises:
            HTTPForbidden: If user doesn't have required permission
        """
        pass

    @staticmethod
    def _is_admin(token, config):
        return config.ROLE_ADMIN in token.get("roles", [])

    @staticmethod
    def _validate_pagination(offset, size):
        if offset < 0:
            raise HTTPBadRequest("offset must be >= 0")
        if size < 1:
            raise HTTPBadRequest("size must be >= 1")
        if size > MAX_SIZE:
            raise HTTPBadRequest(f"size must be <= {MAX_SIZE}")

    @staticmethod
    def get_resources(token, breadcrumb, offset=DEFAULT_OFFSET, size=DEFAULT_SIZE):
        """
        Get a paginated array of resource documents.

        Args:
            token: Authentication token
            breadcrumb: Audit breadcrumb
            offset: Zero-based start index
            size: Number of documents to return

        Returns:
            list: Resource documents

        Raises:
            HTTPBadRequest: If invalid parameters provided
        """
        try:
            ResourceService._check_permission(token, "read")
            ResourceService._validate_pagination(offset, size)

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection = mongo.get_collection(config.RESOURCE_COLLECTION_NAME)

            query = {}
            if not ResourceService._is_admin(token, config):
                query["status"] = {"$ne": ARCHIVED_STATUS}

            cursor = collection.find(query).sort("name", 1).skip(offset).limit(size)
            resources = list(cursor)

            logger.info(
                f"Retrieved {len(resources)} resources (offset={offset}, size={size}) "
                f"for user {token.get('user_id')}"
            )
            return resources
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(f"Error retrieving resources: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve resources")

    @staticmethod
    def get_resource(resource_id, token, breadcrumb):
        """
        Retrieve a resource detail composite.

        Args:
            resource_id: The resource ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            dict: {resource, aggregation, notes}

        Raises:
            HTTPNotFound: If resource is not found
        """
        try:
            ResourceService._check_permission(token, "read")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            resource = mongo.get_document(config.RESOURCE_COLLECTION_NAME, resource_id)
            if resource is None:
                raise HTTPNotFound(f"Resource { resource_id} not found")

            from src.services.aggregation_service import AggregationService
            from src.services.note_service import NoteService

            aggregation = AggregationService.get_aggregation_for_resource(
                resource_id, token, breadcrumb
            )
            notes = NoteService.get_notes_for_resource(resource_id, token, breadcrumb)

            logger.info(
                f"Retrieved resource detail { resource_id} for user {token.get('user_id')}"
            )
            return {
                "resource": resource,
                "aggregation": aggregation,
                "notes": notes,
            }
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving resource { resource_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve resource { resource_id}")
