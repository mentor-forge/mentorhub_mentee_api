"""
Unit tests for Journey service.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId

from src.services.journey_service import JourneyService, TEMPLATE_JOURNEY_ID
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)


class TestJourneyService(unittest.TestCase):
    """Test cases for JourneyService."""

    def setUp(self):
        self.profile_id = "A00000000000000000000099"
        self.mock_token = {
            "user_id": "test_user",
            "roles": ["admin"],
            "profile_id": self.profile_id,
        }
        self.mentee_token = {
            "user_id": "mentee_user",
            "roles": ["mentee"],
            "profile_id": self.profile_id,
        }
        self.other_token = {
            "user_id": "other_user",
            "roles": ["mentee"],
            "profile_id": "A00000000000000000000088",
        }
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }
        self.template_journey = {
            "_id": TEMPLATE_JOURNEY_ID,
            "status": "active",
            "library": [],
            "now": [],
            "next": [
                {
                    "name": "Mindset",
                    "topics": [
                        {
                            "name": "Topic1",
                            "resources": ["507f1f77bcf86cd799439011"],
                        }
                    ],
                }
            ],
            "later": ["C00000000000000000000006"],
        }

    def _mock_config(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.JOURNEY_COLLECTION_NAME = "Journey"
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.EVENT_TYPE_ADVANCED = "advanced"
        mock_config.EVENT_TYPE_COMPLETED = "completed"
        mock_config.ROLE_MENTEE = "mentee"
        mock_get_config.return_value = mock_config
        return mock_config

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_my_journey_existing(self, mock_get_mongo, mock_get_config):
        self._mock_config(mock_get_config)
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": self.profile_id,
            "profile_id": self.profile_id,
            "status": "active",
        }
        mock_get_mongo.return_value = mock_mongo

        result = JourneyService.get_my_journey(self.mock_token, self.mock_breadcrumb)

        self.assertEqual(result["_id"], self.profile_id)
        mock_mongo.get_document.assert_called_with("Journey", self.profile_id)

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_my_journey_creates_from_template(
        self, mock_get_mongo, mock_get_config
    ):
        self._mock_config(mock_get_config)
        created = {
            "_id": self.profile_id,
            "profile_id": self.profile_id,
            "status": "active",
            "next": self.template_journey["next"],
        }
        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = [None, self.template_journey, created]
        mock_get_mongo.return_value = mock_mongo

        result = JourneyService.get_my_journey(self.mock_token, self.mock_breadcrumb)

        self.assertEqual(result["_id"], self.profile_id)
        mock_mongo.create_document.assert_called_once()

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_my_journey_missing_profile_id(self, mock_get_mongo, mock_get_config):
        self._mock_config(mock_get_config)
        mock_get_mongo.return_value = MagicMock()

        with self.assertRaises(HTTPBadRequest):
            JourneyService.get_my_journey(
                {"user_id": "x", "roles": []}, self.mock_breadcrumb
            )

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_my_journey_missing_template(self, mock_get_mongo, mock_get_config):
        self._mock_config(mock_get_config)
        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = [None, None]
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            JourneyService.get_my_journey(self.mock_token, self.mock_breadcrumb)

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_update_journey_owner_success(self, mock_get_mongo, mock_get_config):
        self._mock_config(mock_get_config)
        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {
            "_id": self.profile_id,
            "status": "archived",
        }
        mock_get_mongo.return_value = mock_mongo

        updated = JourneyService.update_journey(
            self.profile_id,
            {"status": "archived"},
            self.mentee_token,
            self.mock_breadcrumb,
        )

        self.assertEqual(updated["status"], "archived")

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_update_journey_admin_success(self, mock_get_mongo, mock_get_config):
        self._mock_config(mock_get_config)
        mock_mongo = MagicMock()
        mock_mongo.update_document.return_value = {"_id": "other", "status": "active"}
        mock_get_mongo.return_value = mock_mongo

        JourneyService.update_journey(
            "A00000000000000000000088",
            {"status": "active"},
            self.mock_token,
            self.mock_breadcrumb,
        )

        mock_mongo.update_document.assert_called_once()

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_update_journey_forbidden(self, mock_get_mongo, mock_get_config):
        self._mock_config(mock_get_config)
        mock_get_mongo.return_value = MagicMock()

        with self.assertRaises(HTTPForbidden):
            JourneyService.update_journey(
                self.profile_id,
                {"status": "archived"},
                self.other_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_update_journey_rejects_server_managed_fields(
        self, mock_get_mongo, mock_get_config
    ):
        self._mock_config(mock_get_config)
        mock_get_mongo.return_value = MagicMock()

        with self.assertRaises(HTTPForbidden):
            JourneyService.update_journey(
                self.profile_id,
                {"now": []},
                self.mentee_token,
                self.mock_breadcrumb,
            )

    @patch("src.services.event_service.EventService.create_event")
    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_advance_resource_success(
        self,
        mock_get_mongo,
        mock_get_config,
        mock_get_my_journey,
        mock_create_event,
    ):
        self._mock_config(mock_get_config)
        resource_id = "507f1f77bcf86cd799439011"
        mock_get_my_journey.return_value = {
            "_id": self.profile_id,
            "next": self.template_journey["next"],
            "now": [],
        }
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": ObjectId(resource_id),
            "name": "TestResource",
        }
        mock_mongo.update_document.return_value = {
            "_id": self.profile_id,
            "now": [{"resource_id": "TestResource"}],
            "next": [],
        }
        mock_get_mongo.return_value = mock_mongo

        result = JourneyService.advance_resource(
            resource_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertIn("now", result)
        mock_create_event.assert_called_once()
        self.assertEqual(mock_create_event.call_args[0][0]["type"], "advanced")

    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_advance_resource_not_in_next(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        resource_id = "507f1f77bcf86cd799439011"
        mock_get_my_journey.return_value = {
            "_id": self.profile_id,
            "next": [],
            "now": [],
        }
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": ObjectId(resource_id)}
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            JourneyService.advance_resource(
                resource_id, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.event_service.EventService.create_event")
    @patch("src.services.aggregation_service.AggregationService.add_completion")
    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_complete_resource_success(
        self,
        mock_get_mongo,
        mock_get_config,
        mock_get_my_journey,
        mock_add_completion,
        mock_create_event,
    ):
        self._mock_config(mock_get_config)
        resource_id = "507f1f77bcf86cd799439011"
        mock_get_my_journey.return_value = {
            "_id": self.profile_id,
            "now": [
                {
                    "resource_id": "TestResource",
                    "used": 1,
                    "started": "2024-01-01T00:00:00Z",
                }
            ],
            "library": [],
        }
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": ObjectId(resource_id),
            "name": "TestResource",
        }
        mock_mongo.update_document.return_value = {
            "_id": self.profile_id,
            "now": [],
            "library": [{"resource_id": resource_id}],
        }
        mock_get_mongo.return_value = mock_mongo

        result = JourneyService.complete_resource(
            resource_id,
            {"rating": 4, "note": "Great"},
            self.mentee_token,
            self.mock_breadcrumb,
        )

        self.assertEqual(result["library"][0]["resource_id"], resource_id)
        mock_add_completion.assert_called_once()
        mock_create_event.assert_called_once()
        self.assertEqual(mock_create_event.call_args[0][0]["type"], "completed")

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_create_journey_handles_exception(self, mock_get_mongo, mock_get_config):
        self._mock_config(mock_get_config)
        mock_mongo = MagicMock()
        mock_mongo.create_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            JourneyService.create_journey(
                {"status": "active"}, self.mock_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
