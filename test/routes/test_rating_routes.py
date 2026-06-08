"""
Unit tests for Rating routes.

These tests validate the Flask route layer for the Rating domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.rating_routes import create_rating_routes


class TestRatingRoutes(unittest.TestCase):
    """Test cases for Rating routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_rating_routes(),
            url_prefix="/api/rating",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.rating_routes.create_flask_token")
    @patch("src.routes.rating_routes.create_flask_breadcrumb")
    @patch("src.routes.rating_routes.RatingService.create_rating")
    @patch("src.routes.rating_routes.RatingService.get_rating")
    def test_create_rating_success(
        self,
        mock_get_rating,
        mock_create_rating,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/rating for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_rating.return_value = "123"
        mock_get_rating.return_value = {
            "_id": "123",
            "name": "test-rating",
            "status": "active",
        }

        response = self.client.post(
            "/api/rating",
            json={"name": "test-rating", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_rating.assert_called_once()
        mock_get_rating.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.rating_routes.create_flask_token")
    @patch("src.routes.rating_routes.create_flask_breadcrumb")
    @patch("src.routes.rating_routes.RatingService.get_ratings")
    def test_get_ratings_no_filter(
        self,
        mock_get_ratings,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/rating without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_ratings.return_value = {
            "items": [
                {"_id": "123", "name": "rating1"},
                {"_id": "456", "name": "rating2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/rating")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_ratings.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.rating_routes.create_flask_token")
    @patch("src.routes.rating_routes.create_flask_breadcrumb")
    @patch("src.routes.rating_routes.RatingService.get_ratings")
    def test_get_ratings_with_name_filter(
        self,
        mock_get_ratings,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/rating with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_ratings.return_value = {
            "items": [{"_id": "123", "name": "test-rating"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/rating?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_ratings.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.rating_routes.create_flask_token")
    @patch("src.routes.rating_routes.create_flask_breadcrumb")
    @patch("src.routes.rating_routes.RatingService.get_rating")
    def test_get_rating_success(
        self,
        mock_get_rating,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/rating/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_rating.return_value = {
            "_id": "123",
            "name": "rating1",
        }

        response = self.client.get("/api/rating/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_rating.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.rating_routes.create_flask_token")
    @patch("src.routes.rating_routes.create_flask_breadcrumb")
    @patch("src.routes.rating_routes.RatingService.get_rating")
    def test_get_rating_not_found(
        self,
        mock_get_rating,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/rating/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_rating.side_effect = HTTPNotFound(
            "Rating 999 not found"
        )

        response = self.client.get("/api/rating/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Rating 999 not found")

    @patch("src.routes.rating_routes.create_flask_token")
    def test_create_rating_unauthorized(self, mock_create_token):
        """Test POST /api/rating when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/rating",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
