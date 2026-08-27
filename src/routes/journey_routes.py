"""
Journey routes for Flask API.

Provides endpoints for Journey domain:
- GET /api/journey - Get authenticated user's journey with embedded profile
- GET /api/journey/<journey_id> - Get journey by ID (from shared factory)
- PATCH /api/journey/promote/path/<path_id> - Promote all Path modules to next
- PATCH /api/journey/promote/module/<path_id>/<module_name> - Promote one module to next
- PATCH /api/journey/advance/<resource_id> - Advance resource from next to now
- PATCH /api/journey/complete/<resource_id> - Complete resource in now
- PATCH /api/journey/<journey_id> - Update a journey document
"""

import logging
from flask import jsonify, request
from api_utils.routes.shared_get_routes import create_journey_get_routes
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.journey_service import JourneyService

logger = logging.getLogger(__name__)


def create_journey_routes():
    """
    Create a Flask Blueprint exposing journey endpoints.

    Returns:
        Blueprint: Flask Blueprint with journey routes
    """
    bp = create_journey_get_routes(JourneyService)

    @bp.route("", methods=["GET"])
    @handle_route_exceptions
    def get_my_journey():
        """GET /api/journey - Return the token owner's journey with embedded profile."""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        journey = JourneyService.get_my_journey_detail(token, breadcrumb)
        logger.info(
            f"get_my_journey Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(journey), 200

    @bp.route("/promote/path/<path_id>", methods=["PATCH"])
    @handle_route_exceptions
    def promote_journey_path(path_id):
        """PATCH /api/journey/promote/path/<path_id> - Promote all Path modules to next."""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        journey = JourneyService.promote_path_to_next(path_id, token, breadcrumb)
        logger.info(
            f"promote_journey_path Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(journey), 200

    @bp.route("/promote/module/<path_id>/<module_name>", methods=["PATCH"])
    @handle_route_exceptions
    def promote_journey_module(path_id, module_name):
        """PATCH /api/journey/promote/module/<path_id>/<module_name> - Promote one module to next."""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        journey = JourneyService.promote_module_to_next(
            path_id, module_name, token, breadcrumb
        )
        logger.info(
            f"promote_journey_module Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(journey), 200

    @bp.route("/advance/<resource_id>", methods=["PATCH"])
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

    @bp.route("/complete/<resource_id>", methods=["PATCH"])
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

    @bp.route("/<journey_id>", methods=["PATCH"])
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
    return bp
