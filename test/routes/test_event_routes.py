"""
Unit tests for Event routes (POST only).
"""

import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.event_routes import create_event_routes


class TestEventRoutes(unittest.TestCase):
    """Test cases for Event routes."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_event_routes(),
            url_prefix="/api/event",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }

    @patch("src.routes.event_routes.create_flask_token")
    @patch("src.routes.event_routes.create_flask_breadcrumb")
    @patch("src.routes.event_routes.EventService.create_event")
    def test_create_event_success(
        self,
        mock_create_event,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_event.return_value = {
            "_id": "123",
            "type": "link",
            "created": self.mock_breadcrumb,
        }

        response = self.client.post(
            "/api/event",
            json={"type": "link"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_event.assert_called_once()

    @patch("src.routes.event_routes.create_flask_token")
    def test_create_event_unauthorized(self, mock_create_token):
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/event",
            json={"type": "link"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)

    @patch("api_utils.routes.shared_get_routes.create_flask_token")
    @patch("api_utils.routes.shared_get_routes.create_flask_breadcrumb")
    @patch("src.services.event_service.EventService.get_events")
    def test_get_events_success(
        self, mock_get_events, mock_create_breadcrumb, mock_create_token
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_get_events.return_value = [
            {"_id": "123", "type": "link", "created": self.mock_breadcrumb}
        ]

        response = self.client.get("/api/event")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        mock_get_events.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            0,
            20,
            {},
            [("created.at_time", -1), ("_id", -1)],
        )


if __name__ == "__main__":
    unittest.main()
