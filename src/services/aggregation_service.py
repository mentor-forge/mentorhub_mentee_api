"""
Aggregation service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Resource_Aggregation domain.
"""

from bson import ObjectId
from bson.errors import InvalidId
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPInternalServerError,
)
import logging

logger = logging.getLogger(__name__)


class AggregationService:
    """
    Service class for Resource_Aggregation domain operations.
    """

    @staticmethod
    def _check_permission(token, operation):
        """Any authenticated user may read aggregation data."""
        pass

    @staticmethod
    def get_aggregation_for_resource(resource_id, token, breadcrumb):
        """
        Retrieve aggregation metrics for a resource.

        Args:
            resource_id: The resource ID to look up
            token: Authentication token
            breadcrumb: Audit breadcrumb

        Returns:
            dict or None: The aggregation document, or None if none exists
        """
        try:
            AggregationService._check_permission(token, "read")

            try:
                resource_object_id = ObjectId(resource_id)
            except (InvalidId, TypeError):
                raise HTTPBadRequest("resource_id must be a valid MongoDB ObjectId")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection = mongo.get_collection(
                config.RESOURCE_AGGREGATION_COLLECTION_NAME
            )
            aggregation = collection.find_one({"resource_id": resource_object_id})

            logger.info(
                f"Retrieved aggregation for resource {resource_id} "
                f"for user {token.get('user_id')}"
            )
            return aggregation
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving aggregation for resource {resource_id}: {str(e)}"
            )
            raise HTTPInternalServerError(
                f"Failed to retrieve aggregation for resource {resource_id}"
            )
