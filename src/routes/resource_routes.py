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
from api_utils.flask_utils.list_request import parse_list_request
from api_utils.services.resource_service import (
    RESOURCE_LIST_FILTERS,
    RESOURCE_LIST_ORDER,
    ResourceService,
)

import logging

logger = logging.getLogger(__name__)


def create_resource_routes():
    """
    Create a Flask Blueprint exposing resource endpoints.

    Returns:
        Blueprint: Flask Blueprint with resource routes
    """
    resource_routes = Blueprint("resource_routes", __name__)

    @resource_routes.route("", methods=["GET"])
    @handle_route_exceptions
    def get_resources():
        """
        GET /api/resource - Retrieve a paginated array of resource documents.

        Headers:
            offset: Zero-based start index (default: 0)
            size: Page size (default: 20, max: 100)

        Query params:
            name, description, status, url, interests, technologies, skill_level: optional filters
            sort_by, order: optional sort (default name asc)

        Returns:
            JSON array of resource documents
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        offset, size, filters, sort_by = parse_list_request(
            request, RESOURCE_LIST_FILTERS, RESOURCE_LIST_ORDER
        )

        resources = ResourceService.get_resources(
            token,
            breadcrumb,
            offset,
            size,
            filters,
            sort_by,
        )

        logger.info(
            f"get_resources Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(resources), 200

    @resource_routes.route("/<resource_id>", methods=["GET"])
    @handle_route_exceptions
    def get_resource(resource_id):
        """
        GET /api/resource/<id> - Retrieve a resource detail composite.

        Args:
            resource_id: The resource ID to retrieve

        Returns:
            JSON response with resource, aggregation, and notes
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        resource = ResourceService.get_resource(resource_id, token, breadcrumb)
        logger.info(
            f"get_resource Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(resource), 200

    logger.info("Resource Flask Routes Registered")
    return resource_routes
