"""
Unit tests for Aggregation service.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.aggregation_service import AggregationService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPInternalServerError,
)


class TestAggregationService(unittest.TestCase):
    """Test cases for AggregationService."""

    def setUp(self):
        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mentee_token = {"user_id": "mentee_user", "roles": ["mentee"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }
        self.resource_id = "507f1f77bcf86cd799439011"

    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_get_aggregation_for_resource_success(
        self, mock_get_mongo, mock_get_config
    ):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": ObjectId(self.resource_id),
            "note_count": 3,
        }
        mock_get_mongo.return_value = mock_mongo

        result = AggregationService.get_aggregation_for_resource(
            self.resource_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result["note_count"], 3)
        mock_mongo.get_document.assert_called_once_with(
            "Resource_Aggregation", self.resource_id
        )

    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_get_aggregation_for_resource_not_found(
        self, mock_get_mongo, mock_get_config
    ):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_mongo.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo

        result = AggregationService.get_aggregation_for_resource(
            self.resource_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNone(result)

    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_get_aggregation_for_resource_invalid_id(
        self, mock_get_mongo, mock_get_config
    ):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest):
            AggregationService.get_aggregation_for_resource(
                "invalid", self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.note_service.NoteService.get_notes_for_resource")
    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_get_aggregation_detail_existing(
        self, mock_get_mongo, mock_get_config, mock_get_notes
    ):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_get_config.return_value = mock_config

        aggregation_doc = {
            "_id": ObjectId(self.resource_id),
            "hits": 2,
        }

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = aggregation_doc
        mock_get_mongo.return_value = mock_mongo
        mock_get_notes.return_value = [{"_id": "note1", "note": "helpful"}]

        result = AggregationService.get_aggregation_detail(
            self.resource_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result["aggregation"]["hits"], 2)
        self.assertEqual(len(result["notes"]), 1)
        mock_get_notes.assert_called_once_with(
            self.resource_id, self.mock_token, self.mock_breadcrumb
        )

    @patch("src.services.note_service.NoteService.get_notes_for_resource")
    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_get_aggregation_detail_creates_when_missing(
        self, mock_get_mongo, mock_get_config, mock_get_notes
    ):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_get_config.return_value = mock_config

        created_doc = {
            "_id": ObjectId(self.resource_id),
            "note_count": 0,
            "hits": 0,
            "rating_sum": 0,
        }

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = [None, created_doc]
        mock_mongo.get_documents.return_value = []
        mock_mongo.create_document.return_value = self.resource_id
        mock_get_mongo.return_value = mock_mongo
        mock_get_notes.return_value = []

        result = AggregationService.get_aggregation_detail(
            self.resource_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result["aggregation"]["rating_sum"], 0)
        self.assertEqual(result["notes"], [])
        mock_mongo.create_document.assert_called_once()

    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_add_completion_requires_mentee_role(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_config.ROLE_MENTEE = "mentee"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPForbidden):
            AggregationService.add_completion(
                self.resource_id,
                5,
                "great resource",
                "PT30M",
                self.mock_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.note_service.NoteService.create_note")
    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_add_completion_increments_counters(
        self, mock_get_mongo, mock_get_config, mock_create_note
    ):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_config.ROLE_MENTEE = "mentee"
        mock_get_config.return_value = mock_config

        aggregation_doc = {
            "_id": ObjectId(self.resource_id),
            "completions": 1,
            "rating_count": 1,
            "rating_sum": 4,
            "note_count": 0,
            "duration": "PT1H",
        }
        updated_doc = {
            **aggregation_doc,
            "completions": 2,
            "rating_count": 2,
            "rating_sum": 9,
            "note_count": 1,
            "duration": "PT1H30M",
        }

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = aggregation_doc
        mock_mongo.update_document.return_value = updated_doc
        mock_get_mongo.return_value = mock_mongo
        mock_create_note.return_value = "note-id"

        result = AggregationService.add_completion(
            self.resource_id,
            5,
            "great resource",
            "PT30M",
            self.mentee_token,
            self.mock_breadcrumb,
        )

        self.assertEqual(result["completions"], 2)
        self.assertEqual(result["rating_sum"], 9)
        self.assertEqual(result["note_count"], 1)
        mock_create_note.assert_called_once()

    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_add_hit_increments_hits(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_get_config.return_value = mock_config

        aggregation_doc = {
            "_id": ObjectId(self.resource_id),
            "hits": 3,
        }
        updated_doc = {**aggregation_doc, "hits": 4}

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = aggregation_doc
        mock_mongo.update_document.return_value = updated_doc
        mock_get_mongo.return_value = mock_mongo

        result = AggregationService.add_hit(
            self.resource_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result["hits"], 4)

    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_get_aggregation_for_resource_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            AggregationService.get_aggregation_for_resource(
                self.resource_id, self.mock_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
