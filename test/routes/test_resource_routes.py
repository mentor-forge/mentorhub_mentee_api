"""
Unit tests for Resource routes (consume-style, read-only).
"""

import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.resource_routes import create_resource_routes


class TestResourceRoutes(unittest.TestCase):
    """Test cases for Resource routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_resource_routes(),
            url_prefix="/api/resource",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }
        self.default_sort = [("name", 1), ("_id", 1)]

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.get_resources")
    def test_get_resources_success(
        self,
        mock_get_resources,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/resource for successful array response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_resources.return_value = [
            {"_id": "123", "name": "resource1"},
            {"_id": "456", "name": "resource2"},
        ]

        response = self.client.get("/api/resource")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        mock_get_resources.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            0,
            20,
            {},
            self.default_sort,
        )

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.get_resources")
    def test_get_resources_with_pagination_headers(
        self,
        mock_get_resources,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/resource with offset/size headers."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_resources.return_value = [{"_id": "123", "name": "resource1"}]

        response = self.client.get(
            "/api/resource",
            headers={"offset": "5", "size": "10"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        mock_get_resources.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            5,
            10,
            {},
            self.default_sort,
        )

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.get_resources")
    def test_get_resources_with_filter_and_sort_query_params(
        self,
        mock_get_resources,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/resource passes filters and sort_by from query params."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_resources.return_value = []

        response = self.client.get(
            "/api/resource?name=guide&status=active&sort_by=description&order=desc"
        )

        self.assertEqual(response.status_code, 200)
        mock_get_resources.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            0,
            20,
            {"name": "guide", "status": ["active"]},
            [("description", -1), ("_id", -1)],
        )

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.get_resources")
    def test_get_resources_invalid_pagination_returns_400(
        self,
        mock_get_resources,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/resource returns 400 for invalid size header."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        response = self.client.get("/api/resource", headers={"size": "101"})

        self.assertEqual(response.status_code, 400)
        mock_get_resources.assert_not_called()

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.get_resource")
    def test_get_resource_success(
        self,
        mock_get_resource,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/resource/<id> for successful composite response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_resource.return_value = {
            "resource": {"_id": "123", "name": "resource1"},
            "aggregation": {"resource_id": "123", "note_count": 1},
            "notes": [{"_id": "note1", "resource_id": "123"}],
        }

        response = self.client.get("/api/resource/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["resource"]["_id"], "123")
        self.assertIn("aggregation", data)
        self.assertIn("notes", data)
        mock_get_resource.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.resource_routes.create_flask_token")
    @patch("src.routes.resource_routes.create_flask_breadcrumb")
    @patch("src.routes.resource_routes.ResourceService.get_resource")
    def test_get_resource_not_found(
        self,
        mock_get_resource,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/resource/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_resource.side_effect = HTTPNotFound("Resource 999 not found")

        response = self.client.get("/api/resource/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Resource 999 not found")

    @patch("src.routes.resource_routes.create_flask_token")
    def test_get_resources_unauthorized(self, mock_create_token):
        """Test GET /api/resource when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.get("/api/resource")

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
