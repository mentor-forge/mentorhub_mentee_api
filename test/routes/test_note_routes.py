"""
Unit tests for Note routes (create only).
"""

import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.note_routes import create_note_routes


class TestNoteRoutes(unittest.TestCase):
    """Test cases for Note routes."""

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_note_routes(),
            url_prefix="/api/note",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "sometime",
            "correlation_id": "correlation_ID",
        }

    @patch("src.routes.note_routes.create_flask_token")
    @patch("src.routes.note_routes.create_flask_breadcrumb")
    @patch("src.routes.note_routes.NoteService.create_note")
    def test_create_note_success(
        self,
        mock_create_note,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb
        mock_create_note.return_value = {
            "_id": "123",
            "resource_id": "507f1f77bcf86cd799439011",
            "note": "A note",
            "status": "active",
        }

        response = self.client.post(
            "/api/note",
            json={
                "resource_id": "507f1f77bcf86cd799439011",
                "note": "A note",
                "status": "active",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["_id"], "123")

    @patch("src.routes.note_routes.create_flask_token")
    def test_create_note_unauthorized(self, mock_create_token):
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post("/api/note", json={"note": "test"})

        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
