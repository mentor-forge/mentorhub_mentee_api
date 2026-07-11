"""
Note routes for Flask API.

Provides endpoints for Note domain:
- POST /api/note - Create a new note document
"""

from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.note_service import NoteService

import logging

logger = logging.getLogger(__name__)


def create_note_routes():
    """
    Create a Flask Blueprint exposing note endpoints.

    Returns:
        Blueprint: Flask Blueprint with note routes
    """
    note_routes = Blueprint("note_routes", __name__)

    @note_routes.route("", methods=["POST"])
    @handle_route_exceptions
    def create_note():
        """
        POST /api/note - Create a new note document.

        Returns:
            JSON response with the created note document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)

        data = request.get_json() or {}
        note = NoteService.create_note(data, token, breadcrumb)

        logger.info(
            f"create_note Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}"
        )
        return jsonify(note), 201

    logger.info("Note Flask Routes Registered")
    return note_routes
