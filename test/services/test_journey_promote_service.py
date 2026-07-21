"""
Unit tests for JourneyPromoteService.
"""

import unittest
from unittest.mock import MagicMock, patch

from bson import ObjectId

from api_utils.flask_utils.exceptions import HTTPBadRequest, HTTPForbidden, HTTPNotFound
from src.services.journey_promote_service import JourneyPromoteService


class TestJourneyPromoteService(unittest.TestCase):
    """Test cases for JourneyPromoteService."""

    def setUp(self):
        self.profile_id = "A00000000000000000000099"
        self.path_id = "B00000000000000000000001"
        self.mock_token = {
            "user_id": "test_user",
            "profile_id": self.profile_id,
        }
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "correlation_id": "correlation_ID",
        }
        self.path_document = {
            "_id": ObjectId(self.path_id),
            "name": "TestPath",
            "modules": [
                {
                    "name": "ModuleA",
                    "description": "First module",
                    "topics": [
                        {
                            "name": "Topic1",
                            "description": "Topic one",
                            "resources": [ObjectId("507f1f77bcf86cd799439011")],
                        }
                    ],
                },
                {
                    "name": "ModuleB",
                    "description": "Second module",
                    "topics": [],
                },
            ],
        }
        self.journey_document = {
            "_id": self.profile_id,
            "profile_id": self.profile_id,
            "later": [self.path_id],
            "next": [],
        }

    def _mock_config(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.JOURNEY_COLLECTION_NAME = "Journey"
        mock_get_config.return_value = mock_config
        return mock_config

    @patch("src.services.journey_promote_service.JourneyService.get_my_journey")
    @patch("src.services.journey_promote_service.Config.get_instance")
    @patch("src.services.journey_promote_service.MongoIO.get_instance")
    def test_promote_path_to_next_success(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = self.journey_document
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.path_document
        mock_mongo.update_document.return_value = {
            "_id": self.profile_id,
            "later": [],
            "next": [
                {
                    "name": "ModuleA",
                    "topics": [{"resources": ["507f1f77bcf86cd799439011"]}],
                },
                {"name": "ModuleB", "topics": []},
            ],
        }
        mock_get_mongo.return_value = mock_mongo

        result = JourneyPromoteService.promote_path_to_next(
            self.path_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(len(result["next"]), 2)
        self.assertEqual(result["later"], [])
        set_data = mock_mongo.update_document.call_args.kwargs["set_data"]
        self.assertEqual(len(set_data["next"]), 2)
        self.assertEqual(set_data["later"], [])

    @patch("src.services.journey_promote_service.JourneyService.get_my_journey")
    @patch("src.services.journey_promote_service.Config.get_instance")
    @patch("src.services.journey_promote_service.MongoIO.get_instance")
    def test_promote_path_to_next_not_in_later(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = {
            **self.journey_document,
            "later": [],
        }
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.path_document
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            JourneyPromoteService.promote_path_to_next(
                self.path_id, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.journey_promote_service.JourneyService.get_my_journey")
    @patch("src.services.journey_promote_service.Config.get_instance")
    @patch("src.services.journey_promote_service.MongoIO.get_instance")
    def test_promote_path_to_next_no_modules(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = self.journey_document
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            **self.path_document,
            "modules": [],
        }
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest):
            JourneyPromoteService.promote_path_to_next(
                self.path_id, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.journey_promote_service.JourneyService.get_my_journey")
    @patch("src.services.journey_promote_service.Config.get_instance")
    @patch("src.services.journey_promote_service.MongoIO.get_instance")
    def test_promote_module_to_next_success(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = self.journey_document
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.path_document
        mock_mongo.update_document.return_value = {
            "_id": self.profile_id,
            "later": [self.path_id],
            "next": [{"name": "ModuleA", "topics": []}],
        }
        mock_get_mongo.return_value = mock_mongo

        result = JourneyPromoteService.promote_module_to_next(
            self.path_id, "ModuleA", self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result["next"][0]["name"], "ModuleA")
        set_data = mock_mongo.update_document.call_args.kwargs["set_data"]
        self.assertEqual(len(set_data["next"]), 1)
        self.assertNotIn("later", set_data)

    @patch("src.services.journey_promote_service.JourneyService.get_my_journey")
    @patch("src.services.journey_promote_service.Config.get_instance")
    @patch("src.services.journey_promote_service.MongoIO.get_instance")
    def test_promote_module_to_next_duplicate(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = {
            **self.journey_document,
            "next": [{"name": "ModuleA", "topics": []}],
        }
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.path_document
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest):
            JourneyPromoteService.promote_module_to_next(
                self.path_id, "ModuleA", self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.journey_promote_service.JourneyService.get_my_journey")
    @patch("src.services.journey_promote_service.Config.get_instance")
    @patch("src.services.journey_promote_service.MongoIO.get_instance")
    def test_promote_module_to_next_module_not_found(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = self.journey_document
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.path_document
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            JourneyPromoteService.promote_module_to_next(
                self.path_id, "MissingModule", self.mock_token, self.mock_breadcrumb
            )

    def test_promote_path_forbidden_without_profile_id(self):
        with self.assertRaises(HTTPForbidden):
            JourneyPromoteService.promote_path_to_next(
                self.path_id, {"user_id": "test_user"}, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
