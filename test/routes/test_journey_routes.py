"""
Unit tests for Journey routes.

These tests validate the Flask route layer for the Journey domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.journey_routes import create_journey_routes


class TestJourneyRoutes(unittest.TestCase):
    """Test cases for Journey routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_journey_routes(),
            url_prefix="/api/journey",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.create_journey")
    @patch("src.routes.journey_routes.JourneyService.get_journey")
    def test_create_journey_success(
        self,
        mock_get_journey,
        mock_create_journey,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/journey for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_journey.return_value = "123"
        mock_get_journey.return_value = {
            "_id": "123",
            "name": "test-journey",
            "status": "active",
        }

        response = self.client.post(
            "/api/journey",
            json={"name": "test-journey", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_journey.assert_called_once()
        mock_get_journey.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.get_journeys")
    def test_get_journeys_no_filter(
        self,
        mock_get_journeys,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/journey without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_journeys.return_value = {
            "items": [
                {"_id": "123", "name": "journey1"},
                {"_id": "456", "name": "journey2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/journey")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_journeys.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.get_journeys")
    def test_get_journeys_with_name_filter(
        self,
        mock_get_journeys,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/journey with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_journeys.return_value = {
            "items": [{"_id": "123", "name": "test-journey"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/journey?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_journeys.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.get_journey")
    def test_get_journey_success(
        self,
        mock_get_journey,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/journey/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_journey.return_value = {
            "_id": "123",
            "name": "journey1",
        }

        response = self.client.get("/api/journey/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_journey.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.get_journey")
    def test_get_journey_not_found(
        self,
        mock_get_journey,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/journey/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_journey.side_effect = HTTPNotFound(
            "Journey 999 not found"
        )

        response = self.client.get("/api/journey/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Journey 999 not found")

    @patch("src.routes.journey_routes.create_flask_token")
    def test_create_journey_unauthorized(self, mock_create_token):
        """Test POST /api/journey when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/journey",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
