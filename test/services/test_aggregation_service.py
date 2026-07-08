"""
Unit tests for Aggregation service.
"""

import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from src.services.aggregation_service import AggregationService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPInternalServerError,
)


class TestAggregationService(unittest.TestCase):
    """Test cases for AggregationService."""

    def setUp(self):
        self.mock_token = {"user_id": "test_user", "roles": ["developer"]}
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

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = {
            "_id": ObjectId(self.resource_id),
            "resource_id": ObjectId(self.resource_id),
            "note_count": 3,
        }

        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo

        result = AggregationService.get_aggregation_for_resource(
            self.resource_id, self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result["note_count"], 3)
        mock_collection.find_one.assert_called_once_with(
            {"resource_id": ObjectId(self.resource_id)}
        )

    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_get_aggregation_for_resource_not_found(
        self, mock_get_mongo, mock_get_config
    ):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_get_config.return_value = mock_config

        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None

        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
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

    @patch("src.services.aggregation_service.Config.get_instance")
    @patch("src.services.aggregation_service.MongoIO.get_instance")
    def test_get_aggregation_for_resource_handles_exception(
        self, mock_get_mongo, mock_get_config
    ):
        mock_config = MagicMock()
        mock_config.RESOURCE_AGGREGATION_COLLECTION_NAME = "Resource_Aggregation"
        mock_get_config.return_value = mock_config

        mock_collection = MagicMock()
        mock_collection.find_one.side_effect = Exception("Database error")

        mock_mongo = MagicMock()
        mock_mongo.get_collection.return_value = mock_collection
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPInternalServerError):
            AggregationService.get_aggregation_for_resource(
                self.resource_id, self.mock_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
