"""
Rating routes for Flask API.

Provides endpoints for Rating domain:
- POST /api/rating - Create a new rating document
- GET /api/rating - Get all rating documents (with optional ?name= query parameter)
- GET /api/rating/<id> - Get a specific rating document by ID
- PATCH /api/rating/<id> - Update a rating document
"""
from flask import Blueprint, jsonify, request
from api_utils.flask_utils.token import create_flask_token
from api_utils.flask_utils.breadcrumb import create_flask_breadcrumb
from api_utils.flask_utils.route_wrapper import handle_route_exceptions
from src.services.rating_service import RatingService

import logging
logger = logging.getLogger(__name__)


def create_rating_routes():
    """
    Create a Flask Blueprint exposing rating endpoints.
    
    Returns:
        Blueprint: Flask Blueprint with rating routes
    """
    rating_routes = Blueprint('rating_routes', __name__)
    
    @rating_routes.route('', methods=['POST'])
    @handle_route_exceptions
    def create_rating():
        """
        POST /api/rating - Create a new rating document.
        
        Request body (JSON):
        {
            "name": "value",
            "description": "value",
            "status": "active",
            ...
        }
        
        Returns:
            JSON response with the created rating document including _id
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        rating_id = RatingService.create_rating(data, token, breadcrumb)
        rating = RatingService.get_rating(rating_id, token, breadcrumb)
        
        logger.info(f"create_rating Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(rating), 201
    
    @rating_routes.route('', methods=['GET'])
    @handle_route_exceptions
    def get_ratings():
        """
        GET /api/rating - Retrieve infinite scroll batch of sorted, filtered rating documents.
        
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
        result = RatingService.get_ratings(
            token, 
            breadcrumb, 
            name=name,
            after_id=after_id,
            limit=limit,
            sort_by=sort_by,
            order=order
        )
        
        logger.info(f"get_ratings Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(result), 200
    
    @rating_routes.route('/<rating_id>', methods=['GET'])
    @handle_route_exceptions
    def get_rating(rating_id):
        """
        GET /api/rating/<id> - Retrieve a specific rating document by ID.
        
        Args:
            rating_id: The rating ID to retrieve
            
        Returns:
            JSON response with the rating document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        rating = RatingService.get_rating(rating_id, token, breadcrumb)
        logger.info(f"get_rating Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(rating), 200
    
    @rating_routes.route('/<rating_id>', methods=['PATCH'])
    @handle_route_exceptions
    def update_rating(rating_id):
        """
        PATCH /api/rating/<id> - Update a rating document.
        
        Args:
            rating_id: The rating ID to update
            
        Request body (JSON):
        {
            "name": "new_value",
            "description": "new_value",
            "status": "archived",
            ...
        }
        
        Returns:
            JSON response with the updated rating document
        """
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        data = request.get_json() or {}
        rating = RatingService.update_rating(rating_id, data, token, breadcrumb)
        
        logger.info(f"update_rating Success {str(breadcrumb['at_time'])}, {breadcrumb['correlation_id']}")
        return jsonify(rating), 200
    
    logger.info("Rating Flask Routes Registered")
    return rating_routes