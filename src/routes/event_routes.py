"""
Event routes for Flask API.

Provides endpoints for Event domain:
- POST /api/event - Create a new event document
"""

from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.event_service import EventService

import logging

logger = logging.getLogger(__name__)


def create_event_routes():
    """
    Create a Flask Blueprint exposing event endpoints.

    Returns:
        Blueprint: Flask Blueprint with event routes
    """
    event_routes = Blueprint("event_routes", __name__)

    @event_routes.route("", methods=["POST"])
    @handle_route_exceptions
    def create_event():
        """
        POST /api/event - Create a new event document.

        Returns:
            JSON response with the created event document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        event = EventService.create_event(data, token, breadcrumb)

        logger.info(
            f"create_event Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(event), 201

    logger.info("Event Flask Routes Registered")
    return event_routes
