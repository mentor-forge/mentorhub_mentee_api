"""
Unit tests for local JourneyService subclass.
"""

import unittest
from unittest.mock import MagicMock, patch
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
        self.path_id = "B00000000000000000000001"
        self.mock_token = {
            "user_id": "test_user",
            "display_name": "Test User",
            "roles": ["admin"],
            "profile_id": self.profile_id,
        }
        self.mentee_token = {
            "user_id": "mentee_user",
            "display_name": "Mentee User",
            "roles": ["mentee"],
            "profile_id": self.profile_id,
        }
        self.other_token = {
            "user_id": "other_user",
            "display_name": "Other User",
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
        self.journey_with_later = {
            "_id": self.profile_id,
            "profile_id": self.profile_id,
            "later": [self.path_id],
            "next": [],
        }
        self.profile_document = {
            "_id": self.profile_id,
            "name": "test-user",
            "full_name": "Test User",
        }

    def _mock_config(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.JOURNEY_COLLECTION_NAME = "Journey"
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_config.PROFILE_COLLECTION_NAME = "Profile"
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.EVENT_TYPE_ADVANCED = "advanced"
        mock_config.EVENT_TYPE_COMPLETED = "completed"
        mock_config.ROLE_MENTEE = "mentee"
        mock_config.ROLE_ADMIN = "admin"
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
        mock_mongo.get_document.side_effect = [
            None,
            self.template_journey,
            created,
        ]
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
        mock_mongo.update_document.return_value = {
            "_id": "other",
            "status": "active",
        }
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

    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_update_journey_rejects_profile_field(
        self, mock_get_mongo, mock_get_config
    ):
        self._mock_config(mock_get_config)
        mock_get_mongo.return_value = MagicMock()

        with self.assertRaises(HTTPForbidden):
            JourneyService.update_journey(
                self.profile_id,
                {"profile": self.profile_document},
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
                    "resource_id": ObjectId(resource_id),
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

    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_my_journey_detail_success(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = {
            "_id": self.profile_id,
            "profile_id": self.profile_id,
            "status": "active",
        }
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.profile_document
        mock_get_mongo.return_value = mock_mongo

        result = JourneyService.get_my_journey_detail(
            self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result["_id"], self.profile_id)
        self.assertEqual(result["profile"], self.profile_document)
        mock_get_my_journey.assert_called_once_with(
            self.mock_token, self.mock_breadcrumb
        )
        mock_mongo.get_document.assert_called_once_with("Profile", self.profile_id)

    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_get_my_journey_detail_missing_profile(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = {
            "_id": self.profile_id,
            "profile_id": self.profile_id,
            "status": "active",
        }
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            JourneyService.get_my_journey_detail(self.mock_token, self.mock_breadcrumb)

    @patch("src.services.journey_service.JourneyService.get_my_journey")
    def test_get_my_journey_detail_missing_profile_id_on_token(
        self, mock_get_my_journey
    ):
        with self.assertRaises(HTTPBadRequest):
            JourneyService.get_my_journey_detail(
                {"user_id": "test_user"}, self.mock_breadcrumb
            )

    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_promote_path_to_next_success(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = self.journey_with_later
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

        result = JourneyService.promote_path_to_next(
            self.path_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(len(result["next"]), 2)
        self.assertEqual(result["later"], [])
        set_data = mock_mongo.update_document.call_args.kwargs["set_data"]
        self.assertEqual(len(set_data["next"]), 2)
        self.assertEqual(set_data["later"], [])

    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_promote_path_to_next_not_in_later(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = {
            **self.journey_with_later,
            "later": [],
        }
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.path_document
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            JourneyService.promote_path_to_next(
                self.path_id, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_promote_path_to_next_no_modules(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = self.journey_with_later
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            **self.path_document,
            "modules": [],
        }
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest):
            JourneyService.promote_path_to_next(
                self.path_id, self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_promote_module_to_next_success(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = self.journey_with_later
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.path_document
        mock_mongo.update_document.return_value = {
            "_id": self.profile_id,
            "later": [self.path_id],
            "next": [{"name": "ModuleA", "topics": []}],
        }
        mock_get_mongo.return_value = mock_mongo

        result = JourneyService.promote_module_to_next(
            self.path_id, "ModuleA", self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result["next"][0]["name"], "ModuleA")
        set_data = mock_mongo.update_document.call_args.kwargs["set_data"]
        self.assertEqual(len(set_data["next"]), 1)
        self.assertNotIn("later", set_data)

    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_promote_module_to_next_duplicate(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = {
            **self.journey_with_later,
            "next": [{"name": "ModuleA", "topics": []}],
        }
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.path_document
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest):
            JourneyService.promote_module_to_next(
                self.path_id, "ModuleA", self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.journey_service.JourneyService.get_my_journey")
    @patch("src.services.journey_service.Config.get_instance")
    @patch("src.services.journey_service.MongoIO.get_instance")
    def test_promote_module_to_next_module_not_found(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = self.journey_with_later
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.path_document
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            JourneyService.promote_module_to_next(
                self.path_id,
                "MissingModule",
                self.mock_token,
                self.mock_breadcrumb,
            )

    def test_promote_path_forbidden_without_profile_id(self):
        with self.assertRaises(HTTPForbidden):
            JourneyService.promote_path_to_next(
                self.path_id, {"user_id": "test_user"}, self.mock_breadcrumb
            )

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
