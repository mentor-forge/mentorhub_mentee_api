"""
Resource routes for Flask API.

Provides endpoints for Resource domain:
- GET /api/resource - Get all resource documents
- GET /api/resource/<id> - Get a specific resource document by ID
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.resource_service import ResourceService

import logging
logger = logging.getLogger(__name__)


def create_resource_routes():
    """
    Create a Flask Blueprint exposing resource endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with resource routes
    """
    resource_routes = Blueprint('resource_routes', __name__)
    
    @resource_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_resources():
        """
        GET /api/resource - Retrieve infinite scroll batch of sorted, filtered resource documents.
        
        Query Parameters:
            name: Optional name filter
            after_id: Cursor for infinite scroll (ID of last item from previous batch, omit for first request)
            limit: Items per batch (default: 10, max: 100)
            sort_by: Field to sort by (default: 'name')
            order: Sort order 'asc' or 'desc' (default: 'asc')
        
        Returns:
            JSON response with infinite scroll results: {
                'items': [...],
                'limit': int,
                'has_more': bool,
                'next_cursor': str|None
            }
        
        Raises:
            400 Bad Request: If invalid parameters provided
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        # Get query parameters
        name = request.args.get('name')
        after_id = request.args.get('after_id')
        limit = request.args.get('limit', 10, type=int)
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')
        
        # Service layer validates parameters and raises HTTPBadRequest if invalid
        # @handle_route_exceptions decorator will catch and format the exception
        result = ResourceService.get_resources(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_resources Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @resource_routes.route('/<resource_id>', methods=['GET'])
    @handle_route_exceptions
    def get_resource(resource_id):
        """
        GET /api/resource/<id> - Retrieve a specific resource document by ID.
        
        Args:
            resource_id: The resource ID to retrieve
            
        Returns:
            JSON response with the resource document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        resource = ResourceService.get_resource(resource_id, token, breadcrumb)
        logger.info(f"get_resource Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(resource), 200
    
    logger.info("Resource Flask Routes Registered")
    return resource_routes