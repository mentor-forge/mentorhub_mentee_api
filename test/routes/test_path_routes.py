"""
Unit tests for Path routes (consume-style, read-only).
"""

import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.path_routes import create_path_routes


class TestPathRoutes(unittest.TestCase):
    """Test cases for Path routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_path_routes(),
            url_prefix="/api/path",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }
        self.default_sort = [("name", 1), ("_id", 1)]

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.get_paths")
    def test_get_paths_success(
        self,
        mock_get_paths,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/path for successful paginated array response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_paths.return_value = [
            {"_id": "123", "name": "path1"},
            {"_id": "456", "name": "path2"},
        ]

        response = self.client.get("/api/path")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        mock_get_paths.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            0,
            20,
            {},
            self.default_sort,
        )

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.get_paths")
    def test_get_paths_with_pagination_headers(
        self,
        mock_get_paths,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/path with offset/size headers."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_paths.return_value = [{"_id": "123", "name": "path1"}]

        response = self.client.get(
            "/api/path",
            headers={"offset": "2", "size": "5"},
        )

        self.assertEqual(response.status_code, 200)
        mock_get_paths.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            2,
            5,
            {},
            self.default_sort,
        )

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.get_paths")
    def test_get_paths_with_name_filter(
        self,
        mock_get_paths,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/path passes name filter from query params."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_paths.return_value = []

        response = self.client.get("/api/path?name=onboard")

        self.assertEqual(response.status_code, 200)
        mock_get_paths.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            0,
            20,
            {"name": "onboard"},
            self.default_sort,
        )

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.get_paths")
    def test_get_paths_invalid_pagination_returns_400(
        self,
        mock_get_paths,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/path returns 400 for invalid offset header."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        response = self.client.get("/api/path", headers={"offset": "-1"})

        self.assertEqual(response.status_code, 400)
        mock_get_paths.assert_not_called()

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.get_path")
    def test_get_path_success(
        self,
        mock_get_path,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/path/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_path.return_value = {
            "_id": "123",
            "name": "path1",
            "modules": [
                {
                    "name": "module1",
                    "topics": [
                        {
                            "name": "topic1",
                            "resources": [
                                {
                                    "_id": "507f1f77bcf86cd799439011",
                                    "name": "resource1",
                                    "description": "desc",
                                }
                            ],
                        }
                    ],
                }
            ],
        }

        response = self.client.get("/api/path/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        resource = data["modules"][0]["topics"][0]["resources"][0]
        self.assertEqual(resource["name"], "resource1")
        self.assertEqual(resource["description"], "desc")
        mock_get_path.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.path_routes.create_flask_token")
    @patch("src.routes.path_routes.create_flask_breadcrumb")
    @patch("src.routes.path_routes.PathService.get_path")
    def test_get_path_not_found(
        self,
        mock_get_path,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/path/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_path.side_effect = HTTPNotFound("Path 999 not found")

        response = self.client.get("/api/path/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Path 999 not found")

    @patch("src.routes.path_routes.create_flask_token")
    def test_get_paths_unauthorized(self, mock_create_token):
        """Test GET /api/path when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.get("/api/path")

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
