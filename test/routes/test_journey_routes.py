"""
Unit tests for Journey routes.
"""

import unittest
from unittest.mock import patch
from flask import Flask

from src.routes.journey_routes import create_journey_routes
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPUnauthorized,
)


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
    @patch("src.routes.journey_routes.JourneyService.get_my_journey_detail")
    def test_get_my_journey_success(
        self, mock_get_my_journey_detail, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_my_journey_detail.return_value = {
            "_id": self.profile_id,
            "profile_id": self.profile_id,
            "status": "active",
            "profile": {"_id": self.profile_id, "name": "test-user"},
        }

        response = self.client.get("/api/journey")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["_id"], self.profile_id)
        self.assertIn("profile", response.json)
        mock_get_my_journey_detail.assert_called_once_with(
            self.mock_token, self.mock_breadcrumb
        )

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
        self.assertNotIn("profile", response.json)

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.update_journey")
    def test_update_journey_rejects_profile_body(
        self, mock_update_journey, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_update_journey.side_effect = HTTPForbidden("Cannot update profile field")

        response = self.client.patch(
            f"/api/journey/{self.profile_id}",
            json={"profile": {"_id": self.profile_id, "name": "hacker"}},
        )

        self.assertEqual(response.status_code, 403)
        mock_update_journey.assert_called_once_with(
            self.profile_id,
            {"profile": {"_id": self.profile_id, "name": "hacker"}},
            self.mock_token,
            self.mock_breadcrumb,
        )

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
        self.assertNotIn("profile", response.json)
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
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.promote_path_to_next")
    def test_promote_journey_path_success(
        self, mock_promote_path, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        path_id = "B00000000000000000000001"
        mock_promote_path.return_value = {
            "_id": self.profile_id,
            "later": [],
            "next": [{"name": "ModuleA"}],
        }

        response = self.client.patch(f"/api/journey/promote/path/{path_id}")

        self.assertEqual(response.status_code, 200)
        mock_promote_path.assert_called_once_with(
            path_id, self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.promote_module_to_next")
    def test_promote_journey_module_success(
        self, mock_promote_module, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        path_id = "B00000000000000000000001"
        module_name = "Foundations"
        mock_promote_module.return_value = {
            "_id": self.profile_id,
            "next": [{"name": module_name}],
        }

        response = self.client.patch(
            f"/api/journey/promote/module/{path_id}/{module_name}"
        )

        self.assertEqual(response.status_code, 200)
        mock_promote_module.assert_called_once_with(
            path_id, module_name, self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.journey_routes.create_flask_token")
    @patch("src.routes.journey_routes.create_flask_breadcrumb")
    @patch("src.routes.journey_routes.JourneyService.promote_module_to_next")
    def test_promote_journey_module_duplicate(
        self, mock_promote_module, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_promote_module.side_effect = HTTPBadRequest(
            "Module 'Foundations' is already present in journey next scope"
        )

        response = self.client.patch(
            "/api/journey/promote/module/B00000000000000000000001/Foundations"
        )

        self.assertEqual(response.status_code, 400)

    @patch("src.routes.journey_routes.create_flask_token")
    def test_get_my_journey_unauthorized(self, mock_create_token):
        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.get("/api/journey")

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.journey_service.JourneyService.get_journey")
    def test_get_journey_by_id_success(
        self, mock_get_journey, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_journey.return_value = {
            "_id": self.profile_id,
            "status": "active",
        }

        response = self.client.get(f"/api/journey/{self.profile_id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["_id"], self.profile_id)
        mock_get_journey.assert_called_once_with(
            self.profile_id, self.mock_token, self.mock_breadcrumb
        )


if __name__ == "__main__":
    unittest.main()
