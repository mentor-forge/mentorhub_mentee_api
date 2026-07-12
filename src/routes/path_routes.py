"""
Path routes for Flask API.

Provides endpoints for Path domain:
- GET /api/path - Get path documents (paginated)
- GET /api/path/<id> - Get a specific path document by ID
"""

from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.flask_utils.list_request import parse_list_request
from api_utils.services.path_service import (
    PATH_LIST_FILTERS,
    PATH_LIST_ORDER,
    PathService,
)

import logging

logger = logging.getLogger(__name__)


def create_path_routes():
    """
    Create a Flask Blueprint exposing path endpoints.

    Returns:
        Blueprint: Flask Blueprint with path routes
    """
    path_routes = Blueprint("path_routes", __name__)

    @path_routes.route("", methods=["GET"])
    @handle_route_exceptions
    def get_paths():
        """
        GET /api/path - Retrieve a paginated array of path documents.

        Headers:
            offset: Zero-based start index (default: 0)
            size: Page size (default: 20, max: 100)

        Query params:
            name: optional case-insensitive substring filter
            sort_by, order: optional sort (default name asc)

        Returns:
            JSON array of Path documents
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        offset, size, filters, sort_by = parse_list_request(
            request, PATH_LIST_FILTERS, PATH_LIST_ORDER
        )

        paths = PathService.get_paths(
            token,
            breadcrumb,
            offset,
            size,
            filters,
            sort_by,
        )

        logger.info(
            f"get_paths Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(paths), 200

    @path_routes.route("/<path_id>", methods=["GET"])
    @handle_route_exceptions
    def get_path(path_id):
        """
        GET /api/path/<id> - Retrieve a specific path document by ID.

        Args:
            path_id: The path ID to retrieve

        Returns:
            JSON response with the path document and enriched resources
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        path = PathService.get_path(path_id, token, breadcrumb)
        logger.info(
            f"get_path Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(path), 200

    logger.info("Path Flask Routes Registered")
    return path_routes
