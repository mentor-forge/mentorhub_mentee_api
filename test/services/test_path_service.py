"""
Unit tests for Path service (consume-style, read-only).
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.path_service import PathService
from api_utils.flask_utils.exceptions import (
    HTTPNotFound,
    HTTPInternalServerError,
)


class TestPathService(unittest.TestCase):
    """Test cases for PathService."""

    def setUp(self):
        """Set up the test fixture."""
        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "by_user": "test_user",
            "from_ip": "127.0.0.1",
            "correlation_id": "test-correlation-id",
        }

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_paths_returns_sorted_list(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of all paths as a list."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_documents.return_value = [
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "alpha"},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "beta"},
        ]
        mock_get_mongo.return_value = mock_mongo

        result = PathService.get_paths(self.mock_token, self.mock_breadcrumb)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        mock_mongo.get_documents.assert_called_once()
        call_kwargs = mock_mongo.get_documents.call_args[1]
        self.assertEqual(call_kwargs["sort_by"], [("name", 1)])

    @patch("src.services.resource_service.ResourceService.get_resources_by_ids")
    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_path_enriches_resources(
        self,
        mock_get_mongo,
        mock_get_config,
        mock_get_resources_by_ids,
    ):
        """Test get_path enriches nested resources with summaries."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        resource_id = "507f1f77bcf86cd799439011"
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "path1",
            "modules": [
                {
                    "name": "module1",
                    "topics": [
                        {
                            "name": "topic1",
                            "resources": [resource_id],
                        }
                    ],
                }
            ],
        }
        mock_get_mongo.return_value = mock_mongo
        mock_get_resources_by_ids.return_value = [
            {
                "_id": resource_id,
                "name": "resource1",
                "description": "desc",
            }
        ]

        result = PathService.get_path("123", self.mock_token, self.mock_breadcrumb)

        self.assertEqual(result["_id"], "123")
        resource = result["modules"][0]["topics"][0]["resources"][0]
        self.assertEqual(resource["_id"], resource_id)
        self.assertEqual(resource["name"], "resource1")
        self.assertEqual(resource["description"], "desc")
        mock_get_resources_by_ids.assert_called_once_with(
            [resource_id], self.mock_token, self.mock_breadcrumb
        )

    @patch("src.services.resource_service.ResourceService.get_resources_by_ids")
    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_path_omits_missing_resources(
        self,
        mock_get_mongo,
        mock_get_config,
        mock_get_resources_by_ids,
    ):
        """Test get_path omits resource IDs with no accessible summary."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "path1",
            "modules": [
                {
                    "topics": [
                        {
                            "resources": [
                                "507f1f77bcf86cd799439011",
                                "507f1f77bcf86cd799439012",
                            ]
                        }
                    ]
                }
            ],
        }
        mock_get_mongo.return_value = mock_mongo
        mock_get_resources_by_ids.return_value = [
            {
                "_id": "507f1f77bcf86cd799439011",
                "name": "resource1",
                "description": "desc",
            }
        ]

        result = PathService.get_path("123", self.mock_token, self.mock_breadcrumb)

        resources = result["modules"][0]["topics"][0]["resources"]
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["_id"], "507f1f77bcf86cd799439011")

    @patch("src.services.resource_service.ResourceService.get_resources_by_ids")
    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_path_without_modules(
        self,
        mock_get_mongo,
        mock_get_config,
        mock_get_resources_by_ids,
    ):
        """Test get_path handles paths with no modules."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {"_id": "123", "name": "path1"}
        mock_get_mongo.return_value = mock_mongo
        mock_get_resources_by_ids.return_value = []

        result = PathService.get_path("123", self.mock_token, self.mock_breadcrumb)

        self.assertEqual(result["_id"], "123")
        mock_get_resources_by_ids.assert_called_once_with(
            [], self.mock_token, self.mock_breadcrumb
        )

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_path_not_found(self, mock_get_mongo, mock_get_config):
        """Test get_path raises HTTPNotFound when document not found."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound) as context:
            PathService.get_path("999", self.mock_token, self.mock_breadcrumb)
        self.assertIn("999", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_paths_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_paths handles exceptions properly."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_documents.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PathService.get_paths(self.mock_token, self.mock_breadcrumb)

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_path_handles_exception(self, mock_get_mongo, mock_get_config):
        """Test get_path handles exceptions properly."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PathService.get_path("123", self.mock_token, self.mock_breadcrumb)

    def test_check_permission_placeholder(self):
        """Test that _check_permission is a placeholder that allows all operations."""
        PathService._check_permission(self.mock_token, "read")
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
