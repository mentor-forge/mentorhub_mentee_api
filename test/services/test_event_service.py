"""
Unit tests for Event service.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.services.event_service import EventService
from api_utils.flask_utils.exceptions import HTTPNotFound, HTTPInternalServerError


class TestEventService(unittest.TestCase):
    """Test cases for EventService."""

    def setUp(self):
        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_success(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"type": "link", "context": {"profile_id": "507f1f77bcf86cd799439011"}}

        event_id = EventService.create_event(
            data, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(event_id, "123")
        created_data = mock_mongo.create_document.call_args[0][1]
        self.assertIn("created", created_data)
        self.assertEqual(created_data["type"], "link")

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_removes_id(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {"_id": "should-be-removed", "type": "link"}

        EventService.create_event(data, self.mock_token, self.mock_breadcrumb)

        created_data = mock_mongo.create_document.call_args[0][1]
        self.assertNotIn("_id", created_data)

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_get_event_success(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "type": "link"}
        mock_get_mongo.return_value = mock_mongo

        event = EventService.get_event("123", self.mock_token, self.mock_breadcrumb)

        self.assertEqual(event["_id"], "123")

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_get_event_not_found(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            EventService.get_event("999", self.mock_token, self.mock_breadcrumb)

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_handles_exception(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            EventService.create_event(
                {"type": "link"}, self.mock_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
