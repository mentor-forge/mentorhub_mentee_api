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
        self.mock_token = {
            "user_id": "test_user",
            "name": "Test User",
            "roles": ["admin"],
            "profile_id": "507f1f77bcf86cd799439011",
            "customer_id": "507f1f77bcf86cd799439012",
            "mentor_id": "",
            "remote_ip": "127.0.0.1",
        }
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

        data = {"type": "login"}

        event_id = EventService.create_event(
            data, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(event_id, "123")
        created_data = mock_mongo.create_document.call_args[0][1]
        self.assertIn("created", created_data)
        self.assertEqual(created_data["type"], "login")
        context = created_data["context"]
        for key, value in self.mock_token.items():
            self.assertIn(key, context)
            if key == "profile_id":
                self.assertEqual(str(context[key]), value)
            else:
                self.assertEqual(context[key], value)

    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_event_ignores_client_context(self, mock_get_mongo, mock_get_config):
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        data = {
            "type": "link",
            "context": {"profile_id": "507f1f77bcf86cd799439099"},
        }

        EventService.create_event(data, self.mock_token, self.mock_breadcrumb)

        created_data = mock_mongo.create_document.call_args[0][1]
        context = created_data["context"]
        self.assertEqual(str(context["profile_id"]), self.mock_token["profile_id"])
        self.assertNotEqual(str(context["profile_id"]), "507f1f77bcf86cd799439099")

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

    @patch("src.services.aggregation_service.AggregationService.add_hit")
    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_link_event_calls_add_hit(
        self, mock_get_mongo, mock_get_config, mock_add_hit
    ):
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        token = {**self.mock_token, "resource_id": "507f1f77bcf86cd799439020"}

        EventService.create_event({"type": "link"}, token, self.mock_breadcrumb)

        mock_add_hit.assert_called_once_with(
            "507f1f77bcf86cd799439020", token, self.mock_breadcrumb
        )

    @patch("src.services.aggregation_service.AggregationService.add_hit")
    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_non_link_event_does_not_call_add_hit(
        self, mock_get_mongo, mock_get_config, mock_add_hit
    ):
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        token = {**self.mock_token, "resource_id": "507f1f77bcf86cd799439020"}

        EventService.create_event({"type": "login"}, token, self.mock_breadcrumb)

        mock_add_hit.assert_not_called()

    @patch("src.services.aggregation_service.AggregationService.add_hit")
    @patch("src.services.event_service.Config.get_instance")
    @patch("src.services.event_service.MongoIO.get_instance")
    def test_create_link_event_without_resource_id_skips_add_hit(
        self, mock_get_mongo, mock_get_config, mock_add_hit
    ):
        mock_config = MagicMock()
        mock_config.EVENT_COLLECTION_NAME = "Event"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.create_document.return_value = "123"
        mock_get_mongo.return_value = mock_mongo

        EventService.create_event(
            {"type": "link"}, self.mock_token, self.mock_breadcrumb
        )

        mock_add_hit.assert_not_called()

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
