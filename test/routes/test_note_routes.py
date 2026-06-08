"""
Unit tests for Note routes.

These tests validate the Flask route layer for the Note domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.note_routes import create_note_routes


class TestNoteRoutes(unittest.TestCase):
    """Test cases for Note routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_note_routes(),
            url_prefix="/api/note",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.note_routes.create_flask_token")
    @patch("src.routes.note_routes.create_flask_breadcrumb")
    @patch("src.routes.note_routes.NoteService.create_note")
    @patch("src.routes.note_routes.NoteService.get_note")
    def test_create_note_success(
        self,
        mock_get_note,
        mock_create_note,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/note for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_note.return_value = "123"
        mock_get_note.return_value = {
            "_id": "123",
            "name": "test-note",
            "status": "active",
        }

        response = self.client.post(
            "/api/note",
            json={"name": "test-note", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_note.assert_called_once()
        mock_get_note.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.note_routes.create_flask_token")
    @patch("src.routes.note_routes.create_flask_breadcrumb")
    @patch("src.routes.note_routes.NoteService.get_notes")
    def test_get_notes_no_filter(
        self,
        mock_get_notes,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/note without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_notes.return_value = {
            "items": [
                {"_id": "123", "name": "note1"},
                {"_id": "456", "name": "note2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/note")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_notes.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.note_routes.create_flask_token")
    @patch("src.routes.note_routes.create_flask_breadcrumb")
    @patch("src.routes.note_routes.NoteService.get_notes")
    def test_get_notes_with_name_filter(
        self,
        mock_get_notes,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/note with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_notes.return_value = {
            "items": [{"_id": "123", "name": "test-note"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/note?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_notes.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.note_routes.create_flask_token")
    @patch("src.routes.note_routes.create_flask_breadcrumb")
    @patch("src.routes.note_routes.NoteService.get_note")
    def test_get_note_success(
        self,
        mock_get_note,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/note/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_note.return_value = {
            "_id": "123",
            "name": "note1",
        }

        response = self.client.get("/api/note/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_note.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.note_routes.create_flask_token")
    @patch("src.routes.note_routes.create_flask_breadcrumb")
    @patch("src.routes.note_routes.NoteService.get_note")
    def test_get_note_not_found(
        self,
        mock_get_note,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/note/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_note.side_effect = HTTPNotFound(
            "Note 999 not found"
        )

        response = self.client.get("/api/note/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "Note 999 not found")

    @patch("src.routes.note_routes.create_flask_token")
    def test_create_note_unauthorized(self, mock_create_token):
        """Test POST /api/note when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/note",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
