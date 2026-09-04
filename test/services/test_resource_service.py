"""
Unit tests for local ResourceService subclass.
"""

import unittest
from unittest.mock import MagicMock, patch
from src.services.resource_service import ResourceService


class TestResourceService(unittest.TestCase):
    """Test cases for ResourceService subclass."""

    def setUp(self):
        self.breadcrumb = {
            "by_user": "user1",
            "at_time": "2024-01-01T00:00:00Z",
            "from_ip": "127.0.0.1",
            "correlation_id": "corr-1",
        }
        self.token = {
            "user_id": "user1",
            "display_name": "Test User",
            "profile_id": "507f1f77bcf86cd799439011",
            "roles": ["mentee"],
        }
        self.resource_id = "507f1f77bcf86cd799439012"

    @patch("api_utils.services.ResourceService.get_resource")
    @patch(
        "src.services.aggregation_service.AggregationService.get_aggregation_for_resource"
    )
    @patch("src.services.note_service.NoteService.list_all_notes_for_resource")
    def test_get_resource_composite(
        self, mock_list_notes, mock_get_aggregation, mock_parent_get_resource
    ):
        mock_raw_resource = {
            "_id": self.resource_id,
            "name": "Test Resource",
            "description": "Description",
        }
        mock_aggregation = {
            "_id": self.resource_id,
            "hits": 5,
            "completions": 1,
        }
        mock_notes = [
            {"_id": "note1", "note": "Great resource"},
        ]

        mock_parent_get_resource.return_value = mock_raw_resource
        mock_get_aggregation.return_value = mock_aggregation
        mock_list_notes.return_value = mock_notes

        result = ResourceService.get_resource(
            self.resource_id, self.token, self.breadcrumb
        )

        self.assertEqual(result["resource"], mock_raw_resource)
        self.assertEqual(result["aggregation"], mock_aggregation)
        self.assertEqual(result["notes"], mock_notes)

        mock_parent_get_resource.assert_called_once_with(
            self.resource_id, self.token, self.breadcrumb
        )
        mock_get_aggregation.assert_called_once_with(
            self.resource_id, self.token, self.breadcrumb
        )
        mock_list_notes.assert_called_once_with(
            self.resource_id, self.token, self.breadcrumb
        )

    def test_inherited_methods_exist(self):
        self.assertTrue(hasattr(ResourceService, "get_resources"))
        self.assertTrue(hasattr(ResourceService, "get_resources_by_ids"))


if __name__ == "__main__":
    unittest.main()
