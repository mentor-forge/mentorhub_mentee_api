"""
Unit tests for local NoteService subclass.
"""

import unittest
from unittest.mock import MagicMock, patch
from bson import ObjectId
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPInternalServerError,
)
from src.services.note_service import NoteService


class TestNoteService(unittest.TestCase):
    """Test cases for NoteService subclass."""

    def setUp(self):
        self.breadcrumb = {
            "by_user": "user1",
            "at_time": "2024-01-01T00:00:00Z",
            "from_ip": "127.0.0.1",
            "correlation_id": "corr-1",
        }
        self.profile_id = "507f1f77bcf86cd799439011"
        self.resource_id = "507f1f77bcf86cd799439012"
        self.mentee_token = {
            "user_id": "user1",
            "profile_id": self.profile_id,
            "roles": ["mentee"],
        }
        self.admin_token = {
            "user_id": "admin1",
            "profile_id": "507f1f77bcf86cd799439099",
            "roles": ["admin"],
        }
        self.other_token = {
            "user_id": "other1",
            "profile_id": "507f1f77bcf86cd799439088",
            "roles": ["customer"],
        }

    @patch("src.services.note_service.MongoIO")
    @patch("src.services.note_service.Config")
    def test_create_note_success_mentee(self, mock_config, mock_mongo_io):
        mock_cfg = MagicMock()
        mock_cfg.NOTE_COLLECTION_NAME = "notes"
        mock_cfg.ROLE_ADMIN = "admin"
        mock_cfg.ROLE_MENTEE = "mentee"
        mock_config.get_instance.return_value = mock_cfg

        mock_mongo = MagicMock()
        created_oid = "507f1f77bcf86cd799439033"
        mock_mongo.create_document.return_value = created_oid
        mock_mongo_io.get_instance.return_value = mock_mongo

        data = {
            "resource_id": self.resource_id,
            "note": "Great resource!",
        }

        result = NoteService.create_note(data, self.mentee_token, self.breadcrumb)

        self.assertIn("_id", result)
        self.assertEqual(str(result["_id"]), created_oid)
        self.assertEqual(result["created"], self.breadcrumb)
        self.assertEqual(result["saved"], self.breadcrumb)
        self.assertEqual(str(result["profile_id"]), self.profile_id)
        mock_mongo.create_document.assert_called_once()

    @patch("src.services.note_service.MongoIO")
    @patch("src.services.note_service.Config")
    def test_create_note_forbidden_non_mentee(self, mock_config, mock_mongo_io):
        mock_cfg = MagicMock()
        mock_cfg.ROLE_ADMIN = "admin"
        mock_cfg.ROLE_MENTEE = "mentee"
        mock_config.get_instance.return_value = mock_cfg

        data = {
            "resource_id": self.resource_id,
            "note": "Test note",
        }

        with self.assertRaises(HTTPForbidden):
            NoteService.create_note(data, self.other_token, self.breadcrumb)

    @patch("src.services.note_service.MongoIO")
    @patch("src.services.note_service.Config")
    def test_create_note_forbidden_forged_profile(self, mock_config, mock_mongo_io):
        mock_cfg = MagicMock()
        mock_cfg.ROLE_ADMIN = "admin"
        mock_cfg.ROLE_MENTEE = "mentee"
        mock_config.get_instance.return_value = mock_cfg

        data = {
            "resource_id": self.resource_id,
            "profile_id": "507f1f77bcf86cd799439099",
            "note": "Test note",
        }

        with self.assertRaises(HTTPForbidden):
            NoteService.create_note(data, self.mentee_token, self.breadcrumb)

    @patch("src.services.note_service.MongoIO")
    @patch("src.services.note_service.Config")
    def test_create_note_admin_success(self, mock_config, mock_mongo_io):
        mock_cfg = MagicMock()
        mock_cfg.NOTE_COLLECTION_NAME = "notes"
        mock_cfg.ROLE_ADMIN = "admin"
        mock_cfg.ROLE_MENTEE = "mentee"
        mock_config.get_instance.return_value = mock_cfg

        mock_mongo = MagicMock()
        created_oid = "507f1f77bcf86cd799439044"
        mock_mongo.create_document.return_value = created_oid
        mock_mongo_io.get_instance.return_value = mock_mongo

        data = {
            "resource_id": self.resource_id,
            "profile_id": "507f1f77bcf86cd799439055",
            "note": "Admin note for another profile",
        }

        result = NoteService.create_note(data, self.admin_token, self.breadcrumb)

        self.assertEqual(str(result["_id"]), created_oid)
        self.assertEqual(result["created"], self.breadcrumb)
        mock_mongo.create_document.assert_called_once()

    @patch("src.services.note_service.MongoIO")
    @patch("src.services.note_service.Config")
    def test_create_note_mongo_error(self, mock_config, mock_mongo_io):
        mock_cfg = MagicMock()
        mock_cfg.NOTE_COLLECTION_NAME = "notes"
        mock_cfg.ROLE_ADMIN = "admin"
        mock_cfg.ROLE_MENTEE = "mentee"
        mock_config.get_instance.return_value = mock_cfg

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("DB error")
        mock_mongo_io.get_instance.return_value = mock_mongo

        data = {
            "resource_id": self.resource_id,
            "note": "Test note",
        }

        with self.assertRaises(HTTPInternalServerError):
            NoteService.create_note(data, self.mentee_token, self.breadcrumb)

    def test_inherited_list_methods_exist(self):
        self.assertTrue(hasattr(NoteService, "get_notes_for_resource"))
        self.assertTrue(hasattr(NoteService, "list_all_notes_for_resource"))


if __name__ == "__main__":
    unittest.main()
