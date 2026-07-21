"""
Unit tests for JourneyDetailService.
"""

import unittest
from unittest.mock import MagicMock, patch

from api_utils.flask_utils.exceptions import HTTPBadRequest, HTTPNotFound
from src.services.journey_detail_service import JourneyDetailService


class TestJourneyDetailService(unittest.TestCase):
    """Test cases for JourneyDetailService."""

    def setUp(self):
        self.profile_id = "A00000000000000000000099"
        self.mock_token = {
            "user_id": "test_user",
            "profile_id": self.profile_id,
        }
        self.mock_breadcrumb = {
            "at_time": "2024-01-01T00:00:00Z",
            "correlation_id": "correlation_ID",
        }
        self.journey_document = {
            "_id": self.profile_id,
            "profile_id": self.profile_id,
            "status": "active",
        }
        self.profile_document = {
            "_id": self.profile_id,
            "name": "test-user",
            "full_name": "Test User",
        }

    def _mock_config(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.PROFILE_COLLECTION_NAME = "Profile"
        mock_get_config.return_value = mock_config
        return mock_config

    @patch("src.services.journey_detail_service.JourneyService.get_my_journey")
    @patch("src.services.journey_detail_service.Config.get_instance")
    @patch("src.services.journey_detail_service.MongoIO.get_instance")
    def test_get_my_journey_detail_success(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = self.journey_document
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = self.profile_document
        mock_get_mongo.return_value = mock_mongo

        result = JourneyDetailService.get_my_journey_detail(
            self.mock_token, self.mock_breadcrumb
        )

        self.assertEqual(result["_id"], self.profile_id)
        self.assertEqual(result["profile"], self.profile_document)
        mock_get_my_journey.assert_called_once_with(
            self.mock_token, self.mock_breadcrumb
        )
        mock_mongo.get_document.assert_called_once_with("Profile", self.profile_id)

    @patch("src.services.journey_detail_service.JourneyService.get_my_journey")
    @patch("src.services.journey_detail_service.Config.get_instance")
    @patch("src.services.journey_detail_service.MongoIO.get_instance")
    def test_get_my_journey_detail_missing_profile(
        self, mock_get_mongo, mock_get_config, mock_get_my_journey
    ):
        self._mock_config(mock_get_config)
        mock_get_my_journey.return_value = self.journey_document
        mock_mongo = MagicMock()
        mock_mongo.get_document.return_value = None
        mock_get_mongo.return_value = mock_mongo

        with self.assertRaises(HTTPNotFound):
            JourneyDetailService.get_my_journey_detail(
                self.mock_token, self.mock_breadcrumb
            )

    @patch("src.services.journey_detail_service.JourneyService.get_my_journey")
    def test_get_my_journey_detail_missing_profile_id_on_token(
        self, mock_get_my_journey
    ):
        with self.assertRaises(HTTPBadRequest):
            JourneyDetailService.get_my_journey_detail(
                {"user_id": "test_user"}, self.mock_breadcrumb
            )
        mock_get_my_journey.assert_not_called()

    @patch("src.services.journey_detail_service.JourneyService.get_my_journey")
    def test_get_my_journey_detail_propagates_journey_errors(self, mock_get_my_journey):
        mock_get_my_journey.side_effect = HTTPNotFound("Template journey not found")

        with self.assertRaises(HTTPNotFound):
            JourneyDetailService.get_my_journey_detail(
                self.mock_token, self.mock_breadcrumb
            )


if __name__ == "__main__":
    unittest.main()
