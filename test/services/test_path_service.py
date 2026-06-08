"""
Unit tests for Path service (consume-style, read-only).
"""
import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.path_service import PathService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
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
    def test_get_paths_first_batch(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of first batch (no cursor)."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter(
            [
                {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "path1"},
                {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "path2"},
            ]
        )

        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo

        result = PathService.get_paths(
            self.mock_token, self.mock_breadcrumb, limit=10
        )

        self.assertIn("items", result)
        self.assertIn("limit", result)
        self.assertIn("has_more", result)
        self.assertIn("next_cursor", result)
        self.assertEqual(len(result["items"]), 2)
        self.assertEqual(result["limit"], 10)
        self.assertFalse(result["has_more"])
        self.assertIsNone(result["next_cursor"])

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_paths_with_name_filter(
        self, mock_get_mongo, mock_get_config
    ):
        """Test retrieval of documents with name filter."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter(
            [
                {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "test-path"},
            ]
        )

        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo

        result = PathService.get_paths(
            self.mock_token, self.mock_breadcrumb, name="test"
        )

        self.assertEqual(len(result["items"]), 1)
        find_call = mock_collection.find.call_args[0][0]
        self.assertIn("name", find_call)
        self.assertEqual(find_call["name"]["$regex"], "test")
        self.assertEqual(find_call["name"]["$options"], "i")

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_paths_invalid_limit_too_small(self, mock_get_mongo, mock_get_config):
        """Test get_paths raises HTTPBadRequest for limit < 1."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            PathService.get_paths(
                self.mock_token, self.mock_breadcrumb, limit=0
            )
        self.assertIn("limit must be >= 1", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_paths_invalid_limit_too_large(self, mock_get_mongo, mock_get_config):
        """Test get_paths raises HTTPBadRequest for limit > 100."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            PathService.get_paths(
                self.mock_token, self.mock_breadcrumb, limit=101
            )
        self.assertIn("limit must be <= 100", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_paths_invalid_sort_by(self, mock_get_mongo, mock_get_config):
        """Test get_paths raises HTTPBadRequest for invalid sort_by."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            PathService.get_paths(
                self.mock_token,
                self.mock_breadcrumb,
                sort_by="invalid_field",
            )
        self.assertIn("sort_by must be one of", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_paths_invalid_order(self, mock_get_mongo, mock_get_config):
        """Test get_paths raises HTTPBadRequest for invalid order."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            PathService.get_paths(
                self.mock_token,
                self.mock_breadcrumb,
                order="invalid",
            )
        self.assertIn("order must be 'asc' or 'desc'", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_paths_invalid_after_id(self, mock_get_mongo, mock_get_config):
        """Test get_paths raises HTTPBadRequest for invalid after_id."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config
        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = MagicMock()
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPBadRequest) as context:
            PathService.get_paths(
                self.mock_token,
                self.mock_breadcrumb,
                after_id="invalid",
            )
        self.assertIn("after_id must be a valid MongoDB ObjectId", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_path_success(self, mock_get_mongo, mock_get_config):
        """Test successful retrieval of a specific path document."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = {
            "_id": "123",
            "name": "path1",
        }
        mock_get_mongo.return_value = mock_mongo

        result = PathService.get_path(
            "123", self.mock_token, self.mock_breadcrumb
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["_id"], "123")
        mock_mongo.get_document.assert_called_once_with("Path", "123")

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
            PathService.get_path(
                "999", self.mock_token, self.mock_breadcrumb
            )
        self.assertIn("999", str(context.exception))

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_paths_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        """Test get_paths handles exceptions properly."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_collection = MagicMock()
        mock_collection.find.side_effect = Exception("Database error")

        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PathService.get_paths(
                self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.path_service.Config.get_instance")
    @patch("src.services.path_service.MongoIO.get_instance")
    def test_get_path_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        """Test get_path handles exceptions properly."""
        mock_config = MagicMock()
        mock_config.PATH_COLLECTION_NAME = "Path"
        mock_get_config.return_value = mock_config

        mock_mongo = MagicMock()
        mock_mongo.get_document.side_effect = Exception("Database error")
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            PathService.get_path(
                "123", self.mock_token, self.mock_breadcrumb
            )

    def test_check_permission_placeholder(self):
        """Test that _check_permission is a placeholder that allows all operations."""
        PathService._check_permission(self.mock_token, "read")
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
