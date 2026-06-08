"""
Note routes for Flask API.

Provides endpoints for Note domain:
- POST /api/note - Create a new note document
- GET /api/note - Get all note documents (with optional ?name= query parameter)
- GET /api/note/<id> - Get a specific note document by ID
- PATCH /api/note/<id> - Update a note document
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
    note_routes = Blueprint('note_routes', __name__)
    
    @note_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_note():
        """
        POST /api/note - Create a new note document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created note document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        note_id = NoteService.create_note(data, token, breadcrumb)
        note = NoteService.get_note(note_id, token, breadcrumb)
        
        logger.info(f"create_note Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(note), 201
    
    @note_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_notes():
        """
        GET /api/note - Retrieve infinite scroll batch of sorted, filtered note documents.
        
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
        result = NoteService.get_notes(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_notes Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @note_routes.route('/<note_id>', methods=['GET'])
    @handle_route_exceptions
    def get_note(note_id):
        """
        GET /api/note/<id> - Retrieve a specific note document by ID.
        
        Args:
            note_id: The note ID to retrieve
            
        Returns:
            JSON response with the note document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        note = NoteService.get_note(note_id, token, breadcrumb)
        logger.info(f"get_note Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(note), 200
    
    @note_routes.route('/<note_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_note(note_id):
        """
        PATCH /api/note/<id> - Update a note document.
        
        Args:
            note_id: The note ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated note document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        note = NoteService.update_note(note_id, data, token, breadcrumb)
        
        logger.info(f"update_note Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(note), 200
    
    logger.info("Note Flask Routes Registered")
    return note_routes