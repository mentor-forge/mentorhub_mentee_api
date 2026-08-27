"""
Path routes for Flask API.

Provides endpoints for Path domain:
- GET /api/path - Get path documents (from shared factory)
- GET /api/path/<id> - Get a specific path document with enriched resources (from shared factory)
"""

from api_utils.routes.shared_get_routes import create_path_get_routes
from src.services.path_service import PathService


def create_path_routes():
    """
    Create a Flask Blueprint exposing path endpoints using shared factory.

    Returns:
        Blueprint: Flask Blueprint with path routes
    """
    return create_path_get_routes(PathService)
