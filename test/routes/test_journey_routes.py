"""
Unit tests for Journey routes.
"""

import unittest
from unittest.mock import patch
from flask import Flask

from src.routes.journey_routes import create_journey_routes
from api_utils.flask_utils.exceptions import HTTPForbidden, HTTPUnauthorized


class TestJourneyRoutes(unittest.TestCase):
    """Test cases for Journey routes."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_journey_routes(),
            url_prefix="/api/journey",
        )
        self.client = self.app.test_client()

        self.profile_id = "A00000000000000000000099"
        self.mock_token = {
            "user_id": "test_user",
            "roles": ["admin"],
            "profile_id": self.profile_id,
        }
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.get_my_journey")
    def test_get_my_journey_success(
        self, mock_get_my_journey, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_my_journey.return_value = {
            "_id": self.profile_id,
            "profile_id": self.profile_id,
            "status": "active",
        }

        response = self.client.get("/api/journey")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["_id"], self.profile_id)
        mock_get_my_journey.assert_called_once_with(
            self.mock_token, self.mock_breadcrumb
        )

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
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_create_journey.return_value = "123"
        mock_get_journey.return_value = {"_id": "123", "status": "active"}

        response = self.client.post(
            "/api/journey",
            json={"status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["_id"], "123")

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.update_journey")
    def test_update_journey_success(
        self, mock_update_journey, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_update_journey.return_value = {
            "_id": self.profile_id,
            "status": "archived",
        }

        response = self.client.patch(
            f"/api/journey/{self.profile_id}",
            json={"status": "archived"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "archived")

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.update_journey")
    def test_update_journey_forbidden(
        self, mock_update_journey, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_update_journey.side_effect = HTTPForbidden("Insufficient permissions")

        response = self.client.patch(
            f"/api/journey/{self.profile_id}",
            json={"status": "archived"},
        )

        self.assertEqual(response.status_code, 403)

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.advance_resource")
    def test_advance_journey_resource_success(
        self, mock_advance, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        resource_id = "507f1f77bcf86cd799439011"
        mock_advance.return_value = {"_id": self.profile_id, "now": []}

        response = self.client.patch(f"/api/journey/advance/{resource_id}")

        self.assertEqual(response.status_code, 200)
        mock_advance.assert_called_once_with(
            resource_id, self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.complete_resource")
    def test_complete_journey_resource_success(
        self, mock_complete, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        resource_id = "507f1f77bcf86cd799439011"
        mock_complete.return_value = {"_id": self.profile_id, "library": []}

        response = self.client.patch(
            f"/api/journey/complete/{resource_id}",
            json={"rating": 4},
        )

        self.assertEqual(response.status_code, 200)
        mock_complete.assert_called_once()

    @patch("src.routes.journey_routes.create_flask_token")
    def test_create_journey_unauthorized(self, mock_create_token):
        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/journey",
            json={"status": "active"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
