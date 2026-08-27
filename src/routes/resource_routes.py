"""
Resource routes for Flask API.

Provides endpoints for Resource domain:
- GET /api/resource - Get all resource documents (from shared factory)
- GET /api/resource/<id> - Get a specific resource document detail composite (from shared factory)
"""

from api_utils.routes.shared_get_routes import create_resource_get_routes
from src.services.resource_service import ResourceService


def create_resource_routes():
    """
    Create a Flask Blueprint exposing resource endpoints using shared factory.

    Returns:
        Blueprint: Flask Blueprint with resource routes
    """
    return create_resource_get_routes(ResourceService)
