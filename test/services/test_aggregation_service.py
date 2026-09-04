"""
Unit tests for local AggregationService subclass.
"""

from datetime import timedelta
import unittest
from unittest.mock import MagicMock, patch
from bson import ObjectId
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPInternalServerError,
)
from src.services.aggregation_service import AggregationService


class TestAggregationService(unittest.TestCase):
    """Test cases for AggregationService subclass."""

    def setUp(self):
        self.breadcrumb = {
            "by_user": "user1",
            "at_time": "2024-01-01T00:00:00Z",
            "from_ip": "127.0.0.1",
            "correlation_id": "corr-1",
        }
        self.profile_id = "507f1f77bcf86cd799439011"
        self.resource_id = "507f1f77bcf86cd799439012"
        self.resource_oid = ObjectId(self.resource_id)
        self.mentee_token = {
            "user_id": "user1",
            "display_name": "Test User",
            "profile_id": self.profile_id,
            "roles": ["mentee"],
        }
        self.admin_token = {
            "user_id": "admin1",
            "display_name": "Admin User",
            "profile_id": "507f1f77bcf86cd799439099",
            "roles": ["admin"],
        }
        self.other_token = {
            "user_id": "other1",
            "display_name": "Other User",
            "profile_id": "507f1f77bcf86cd799439088",
            "roles": ["customer"],
        }

    def test_duration_helpers(self):
        self.assertEqual(AggregationService._parse_iso_duration("PT0S"), timedelta(0))
        self.assertEqual(
            AggregationService._parse_iso_duration("PT1H30M"),
            timedelta(hours=1, minutes=30),
        )
        self.assertEqual(
            AggregationService._format_iso_duration(timedelta(hours=1, minutes=30)),
            "PT1H30M",
        )
        self.assertEqual(AggregationService._format_iso_duration(timedelta(0)), "PT0S")
        self.assertEqual(AggregationService._add_durations("PT1H", "PT30M"), "PT1H30M")
        with self.assertRaises(HTTPBadRequest):
            AggregationService._parse_iso_duration("INVALID")

    @patch("src.services.aggregation_service.MongoIO")
    @patch("src.services.aggregation_service.Config")
    def test_add_hit_success(self, mock_config, mock_mongo_io):
        mock_cfg = MagicMock()
        mock_cfg.RESOURCE_AGGREGATION_COLLECTION_NAME = "resource_aggregations"
        mock_config.get_instance.return_value = mock_cfg

        mock_mongo = MagicMock()
        existing_doc = {
            "_id": self.resource_oid,
            "hits": 2,
            "completions": 0,
            "duration": "PT0S",
        }
        mock_mongo.get_document.return_value = existing_doc
        mock_mongo.update_document.return_value = {
            "_id": self.resource_oid,
            "hits": 3,
            "completions": 0,
        }
        mock_mongo_io.get_instance.return_value = mock_mongo

        result = AggregationService.add_hit(
            self.resource_id, self.other_token, self.breadcrumb
        )

        self.assertEqual(result["hits"], 3)
        mock_mongo.update_document.assert_called_once()
        call_kwargs = mock_mongo.update_document.call_args.kwargs
        self.assertEqual(call_kwargs["set_data"]["hits"], 3)

    @patch("src.services.aggregation_service.MongoIO")
    @patch("src.services.aggregation_service.Config")
    def test_add_completion_forbidden_non_mentee(self, mock_config, mock_mongo_io):
        mock_cfg = MagicMock()
        mock_cfg.ROLE_ADMIN = "admin"
        mock_cfg.ROLE_MENTEE = "mentee"
        mock_config.get_instance.return_value = mock_cfg

        with self.assertRaises(HTTPForbidden):
            AggregationService.add_completion(
                self.resource_id, 4, "A note", "PT1H", self.other_token, self.breadcrumb
            )

    @patch("src.services.aggregation_service.MongoIO")
    @patch("src.services.aggregation_service.Config")
    @patch("src.services.note_service.NoteService.create_note")
    def test_add_completion_mentee_success(
        self, mock_create_note, mock_config, mock_mongo_io
    ):
        mock_cfg = MagicMock()
        mock_cfg.RESOURCE_AGGREGATION_COLLECTION_NAME = "resource_aggregations"
        mock_cfg.ROLE_ADMIN = "admin"
        mock_cfg.ROLE_MENTEE = "mentee"
        mock_config.get_instance.return_value = mock_cfg

        mock_mongo = MagicMock()
        existing_doc = {
            "_id": self.resource_oid,
            "completions": 1,
            "rating_count": 1,
            "rating_sum": 3,
            "note_count": 0,
            "duration": "PT30M",
        }
        mock_mongo.get_document.return_value = existing_doc
        mock_mongo.update_document.return_value = {
            "_id": self.resource_oid,
            "completions": 2,
            "rating_count": 2,
            "rating_sum": 7,
            "note_count": 1,
            "duration": "PT1H30M",
        }
        mock_mongo_io.get_instance.return_value = mock_mongo

        result = AggregationService.add_completion(
            self.resource_id,
            4,
            "Learned a lot!",
            "PT1H",
            self.mentee_token,
            self.breadcrumb,
        )

        self.assertEqual(result["completions"], 2)
        mock_create_note.assert_called_once()
        mock_mongo.update_document.assert_called_once()
        call_kwargs = mock_mongo.update_document.call_args.kwargs
        self.assertEqual(call_kwargs["set_data"]["completions"], 2)
        self.assertEqual(call_kwargs["set_data"]["rating_sum"], 7)
        self.assertEqual(call_kwargs["set_data"]["rating_count"], 2)
        self.assertEqual(call_kwargs["set_data"]["note_count"], 1)
        self.assertEqual(call_kwargs["set_data"]["duration"], "PT1H30M")

    @patch("src.services.aggregation_service.MongoIO")
    @patch("src.services.aggregation_service.Config")
    @patch("src.services.note_service.NoteService.list_all_notes_for_resource")
    def test_get_aggregation_detail_success(
        self, mock_list_notes, mock_config, mock_mongo_io
    ):
        mock_cfg = MagicMock()
        mock_cfg.RESOURCE_AGGREGATION_COLLECTION_NAME = "resource_aggregations"
        mock_config.get_instance.return_value = mock_cfg

        mock_mongo = MagicMock()
        existing_doc = {
            "_id": self.resource_oid,
            "hits": 5,
            "completions": 2,
            "duration": "PT1H",
        }
        mock_mongo.get_document.return_value = existing_doc
        mock_mongo_io.get_instance.return_value = mock_mongo

        mock_notes = [
            {"_id": "note1", "note": "First note"},
            {"_id": "note2", "note": "Second note"},
        ]
        mock_list_notes.return_value = mock_notes

        result = AggregationService.get_aggregation_detail(
            self.resource_id, self.mentee_token, self.breadcrumb
        )

        self.assertIn("aggregation", result)
        self.assertIn("notes", result)
        self.assertEqual(result["aggregation"]["_id"], self.resource_oid)
        self.assertEqual(result["notes"], mock_notes)
        mock_list_notes.assert_called_once_with(
            self.resource_id, self.mentee_token, self.breadcrumb
        )


if __name__ == "__main__":
    unittest.main()
