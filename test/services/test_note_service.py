"""
Unit tests for Note service.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.note_service import NoteService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPNotFound,
    HTTPInternalServerError,
)


class TestNoteService(unittest.TestCase):
    """Test cases for NoteService."""

    def setUp(self):
        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }
        self.resource_id = "507f1f77bcf86cd799439011"

    @patch("src.services.note_service.Config.get_instance")
    @patch("src.services.note_service.MongoIO.get_instance")
    def test_create_note_success(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.NOTE_COLLECTION_NAME = "Note"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {
            "resource_id": self.resource_id,
            "note": "Test note",
            "status": "active",
        }

        note_id = NoteService.create_note(data, self.mock_token, self.mock_breadcrumb)

        self.assertEqual(note_id, "123")
        mock_mongo.create_document.assert_called_once()
        created_data = mock_mongo.create_document.call_args[0][1]
        self.assertIn("created", created_data)
        self.assertIn("saved", created_data)
        self.assertEqual(created_data["note"], "Test note")

    @patch("src.services.note_service.Config.get_instance")
    @patch("src.services.note_service.MongoIO.get_instance")
    def test_create_note_removes_id(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.NOTE_COLLECTION_NAME = "Note"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "should-be-removed", "note": "test"}

        NoteService.create_note(data, self.mock_token, self.mock_breadcrumb)

        created_data = mock_mongo.create_document.call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.note_service.Config.get_instance")
    @patch("src.services.note_service.MongoIO.get_instance")
    def test_get_note_success(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.NOTE_COLLECTION_NAME = "Note"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "note": "hello"}
        mock_get_mongo.return_value = mock_mongo

        note = NoteService.get_note("123", self.mock_token, self.mock_breadcrumb)

        self.assertEqual(note["_id"], "123")

    @patch("src.services.note_service.Config.get_instance")
    @patch("src.services.note_service.MongoIO.get_instance")
    def test_get_note_not_found(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.NOTE_COLLECTION_NAME = "Note"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            NoteService.get_note("999", self.mock_token, self.mock_breadcrumb)

    @patch("src.services.note_service.Config.get_instance")
    @patch("src.services.note_service.MongoIO.get_instance")
    def test_get_notes_for_resource_success(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.NOTE_COLLECTION_NAME = "Note"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [{"_id": "1", "note": "a"}]
        mock_get_mongo.return_value = mock_mongo

        notes = NoteService.get_notes_for_resource(
            self.resource_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(len(notes), 1)
        mock_mongo.get_documents.assert_called_once()
        call_kwargs = mock_mongo.get_documents.call_args[1]
        self.assertEqual(
            call_kwargs["match"]["resource_id"], ObjectId(self.resource_id)
        )

    @patch("src.services.note_service.Config.get_instance")
    @patch("src.services.note_service.MongoIO.get_instance")
    def test_get_notes_for_resource_invalid_id(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.NOTE_COLLECTION_NAME = "Note"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest):
            NoteService.get_notes_for_resource(
                "invalid", self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.note_service.Config.get_instance")
    @patch("src.services.note_service.MongoIO.get_instance")
    def test_create_note_handles_exception(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.NOTE_COLLECTION_NAME = "Note"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            NoteService.create_note(
                {"note": "x"}, self.mock_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
