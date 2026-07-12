"""
Journey routes for Flask API.

Provides endpoints for Journey domain:
- GET /api/journey - Get authenticated user's journey (get-or-create)
- POST /api/journey - Create a new journey document
- PATCH /api/journey/advance/<resource_id> - Advance resource from next to now
- PATCH /api/journey/complete/<resource_id> - Complete resource in now
- PATCH /api/journey/<id> - Update a journey document
"""

from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from api_utils.services import JourneyService

import logging

logger = logging.getLogger(__name__)


def create_journey_routes():
    """Create a Flask Blueprint exposing journey endpoints."""
    journey_routes = Blueprint("journey_routes", __name__)

    @journey_routes.route("", methods=["GET"])
    @handle_route_exceptions
    def get_my_journey():
        """GET /api/journey - Return the token owner's journey (get-or-create)."""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        journey = JourneyService.get_my_journey(token, breadcrumb)
        logger.info(
            f"get_my_journey Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(journey), 200

    @journey_routes.route("", methods=["POST"])
    @handle_route_exceptions
    def create_journey():
        """POST /api/journey - Create a new journey document."""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        data = request.get_json() or {}
        journey_id = JourneyService.create_journey(data, token, breadcrumb)
        journey = JourneyService.get_journey(journey_id, token, breadcrumb)
        logger.info(
            f"create_journey Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(journey), 201

    @journey_routes.route("/advance/<resource_id>", methods=["PATCH"])
    @handle_route_exceptions
    def advance_journey_resource(resource_id):
        """PATCH /api/journey/advance/<resource_id> - Move resource from next to now."""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        journey = JourneyService.advance_resource(resource_id, token, breadcrumb)
        logger.info(
            f"advance_journey_resource Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(journey), 200

    @journey_routes.route("/complete/<resource_id>", methods=["PATCH"])
    @handle_route_exceptions
    def complete_journey_resource(resource_id):
        """PATCH /api/journey/complete/<resource_id> - Complete resource in now."""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        data = request.get_json(silent=True) or {}
        journey = JourneyService.complete_resource(resource_id, data, token, breadcrumb)
        logger.info(
            f"complete_journey_resource Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(journey), 200

    @journey_routes.route("/<journey_id>", methods=["PATCH"])
    @handle_route_exceptions
    def update_journey(journey_id):
        """PATCH /api/journey/<id> - Update a journey document."""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        data = request.get_json() or {}
        journey = JourneyService.update_journey(journey_id, data, token, breadcrumb)
        logger.info(
            f"update_journey Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(journey), 200

    logger.info("Journey Flask Routes Registered")
    return journey_routes
