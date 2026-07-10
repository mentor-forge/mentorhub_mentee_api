"""
Unit tests for Resource service (consume-style, read-only).
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.resource_service import ResourceService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)


class TestResourceService(unittest.TestCase):
    """Test cases for ResourceService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mock_admin_token = {"user_id": "admin_user", "roles": ["admin"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    def _mock_config(self):
        mock_config = MagicMock()
        mock_config.RESOURCE_COLLECTION_NAME = "Resource"
        mock_config.ROLE_ADMIN = "admin"
        return mock_config

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_returns_array(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval returns a plain array."""
        mock_get_config.return_value = self._mock_config()

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "resource1"},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "resource2"},
            {"_id": ObjectId("507f1f77bcf86cd799439013"), "name": "resource3"},
        ]
        mock_get_mongo.return_value = mock_mongo

        result = ResourceService.get_resources(
            self.mock_token, self.mock_breadcrumb, offset=0, size=2
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        mock_mongo.get_documents.assert_called_once()
        call_kwargs = mock_mongo.get_documents.call_args[1]
        self.assertEqual(call_kwargs["match"]["status"], {"$ne": "archived"})

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_admin_includes_archived(
        self, mock_get_mongo, mock_get_config
    ):
        """Test admin users do not filter out archived resources."""
        mock_get_config.return_value = self._mock_config()

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = []
        mock_get_mongo.return_value = mock_mongo

        ResourceService.get_resources(
            self.mock_admin_token, self.mock_breadcrumb, offset=0, size=20
        )

        call_kwargs = mock_mongo.get_documents.call_args[1]
        self.assertEqual(call_kwargs["match"], {})

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_invalid_offset(self, mock_get_mongo, mock_get_config):
        """Test get_resources raises HTTPBadRequest for offset < 0."""
        mock_get_config.return_value = self._mock_config()
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            ResourceService.get_resources(
                self.mock_token, self.mock_breadcrumb, offset=-1, size=20
            )
        self.assertIn("offset must be >= 0", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_invalid_size_too_small(
        self, mock_get_mongo, mock_get_config
    ):
        """Test get_resources raises HTTPBadRequest for size < 1."""
        mock_get_config.return_value = self._mock_config()
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            ResourceService.get_resources(
                self.mock_token, self.mock_breadcrumb, offset=0, size=0
            )
        self.assertIn("size must be >= 1", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_invalid_size_too_large(
        self, mock_get_mongo, mock_get_config
    ):
        """Test get_resources raises HTTPBadRequest for size > 100."""
        mock_get_config.return_value = self._mock_config()
        mock_mongo = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            ResourceService.get_resources(
                self.mock_token, self.mock_breadcrumb, offset=0, size=101
            )
        self.assertIn("size must be <= 100", str(context.exception))

    @patch("src.services.note_service.NoteService.get_notes_for_resource")
    @patch(
        "src.services.aggregation_service.AggregationService.get_aggregation_for_resource"
    )
    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resource_returns_composite(
        self,
        mock_get_mongo,
        mock_get_config,
        mock_get_aggregation,
        mock_get_notes,
    ):
        """Test get_resource returns resource detail composite via services."""
        mock_get_config.return_value = self._mock_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "resource1",
        }
        mock_get_mongo.return_value = mock_mongo
        mock_get_aggregation.return_value = {
            "resource_id": "123",
            "note_count": 2,
        }
        mock_get_notes.return_value = [{"_id": "note1", "resource_id": "123"}]

        result = ResourceService.get_resource(
            "123", self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result["resource"]["_id"], "123")
        self.assertEqual(result["aggregation"]["note_count"], 2)
        self.assertEqual(len(result["notes"]), 1)
        mock_get_aggregation.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )
        mock_get_notes.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resource_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_resource raises HTTPNotFound when document not found."""
        mock_get_config.return_value = self._mock_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            ResourceService.get_resource("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resources_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_resources handles exceptions properly."""
        mock_get_config.return_value = self._mock_config()

        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            ResourceService.get_resources(self.mock_token, self.mock_breadcrumb)

    @patch("src.services.resource_service.Config.get_instance")
    @patch("src.services.resource_service.MongoIO.get_instance")
    def test_get_resource_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_resource handles exceptions properly."""
        mock_get_config.return_value = self._mock_config()

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            ResourceService.get_resource("123", self.mock_token, self.mock_breadcrumb)

    def test_check_permission_placeholder(self):
        """Test that _check_permission is a placeholder that allows all operations."""
        ResourceService._check_permission(self.mock_token, "read")
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
