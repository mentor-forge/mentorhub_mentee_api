"""
Resource service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Resource domain.
"""
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import HTTPBadRequest, HTTPForbidden, HTTPNotFound, HTTPInternalServerError
from api_utils.mongo_utils import execute_infinite_scroll_query
import logging

logger = logging.getLogger(__name__)

# Allowed sort fields for Resource domain
ALLOWED_SORT_FIELDS = ['name', 'description']


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
            
        Note: This is a placeholder for future RBAC implementation.
        For now, all operations require a valid token (authentication only).
        
        Example RBAC implementation:
            if operation == 'read':
                # Read requires any authenticated user (no additional check needed)
                # For stricter requirements, you could require specific roles:
                # if not any(role in token.get('roles', []) for role in ['staff', 'admin', 'viewer']):
                #     raise HTTPForbidden("Insufficient permissions to read resource documents")
                pass
        """
        pass
    
    @staticmethod
    def get_resources(token, breadcrumb, name=None, after_id=None, limit=10, sort_by='name', order='asc'):
        """
        Get infinite scroll batch of sorted, filtered resource documents.
        
        Args:
            token: Authentication token
            breadcrumb: Audit breadcrumb
            name: Optional name filter (simple search)
            after_id: Cursor (ID of last item from previous batch, None for first request)
            limit: Items per batch
            sort_by: Field to sort by
            order: Sort order ('asc' or 'desc')
        
        Returns:
            dict: {
                'items': [...],
                'limit': int,
                'has_more': bool,
                'next_cursor': str|None  # ID of last item, or None if no more
            }
        
        Raises:
            HTTPBadRequest: If invalid parameters provided
        """
        try:
            ResourceService._check_permission(token, 'read')
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection = mongo.get_collection(config.RESOURCE_COLLECTION_NAME)
            result = execute_infinite_scroll_query(
                collection,
                name=name,
                after_id=after_id,
                limit=limit,
                sort_by=sort_by,
                order=order,
                allowed_sort_fields=ALLOWED_SORT_FIELDS,
            )
            logger.info(
                f"Retrieved {len(result['items'])} resources (has_more={result['has_more']}) "
                f"for user {token.get('user_id')}"
            )
            return result
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(f"Error retrieving resources: {str(e)}")
            raise HTTPInternalServerError("Failed to retrieve resources")
    
    @staticmethod
    def get_resource(resource_id, token, breadcrumb):
        """
        Retrieve a specific resource document by ID.
        
        Args:
            resource_id: The resource ID to retrieve
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging
            
        Returns:
            dict: The resource document
            
        Raises:
            HTTPNotFound: If resource is not found
        """
        try:
            ResourceService._check_permission(token, 'read')
            
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            resource = mongo.get_document(config.RESOURCE_COLLECTION_NAME, resource_id)
            if resource is None:
                raise HTTPNotFound(f"Resource { resource_id} not found")
            
            logger.info(f"Retrieved resource { resource_id} for user {token.get('user_id')}")
            return resource
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving resource { resource_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve resource { resource_id}")