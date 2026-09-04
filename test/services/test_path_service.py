"""
Unit tests for local PathService subclass.
"""

import unittest
from unittest.mock import MagicMock, patch
from src.services.path_service import PathService


class TestPathService(unittest.TestCase):
    """Test cases for PathService subclass."""

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
        self.path_id = "507f1f77bcf86cd799439020"
        self.resource_id_1 = "507f1f77bcf86cd799439031"
        self.resource_id_2 = "507f1f77bcf86cd799439032"

    @patch("api_utils.services.PathService.get_path")
    @patch("src.services.resource_service.ResourceService.get_resources_by_ids")
    def test_get_path_enriched(self, mock_get_resources, mock_parent_get_path):
        raw_path = {
            "_id": self.path_id,
            "name": "Frontend Path",
            "modules": [
                {
                    "name": "Foundations",
                    "topics": [
                        {
                            "name": "HTML & CSS",
                            "resources": [
                                self.resource_id_1,
                                self.resource_id_2,
                            ],
                        }
                    ],
                }
            ],
        }
        resource_summaries = [
            {
                "_id": self.resource_id_1,
                "name": "HTML Basics",
                "description": "Intro to HTML",
            },
            {
                "_id": self.resource_id_2,
                "name": "CSS Basics",
                "description": "Intro to CSS",
            },
        ]

        mock_parent_get_path.return_value = raw_path
        mock_get_resources.return_value = resource_summaries

        result = PathService.get_path(self.path_id, self.token, self.breadcrumb)

        mock_parent_get_path.assert_called_once_with(
            self.path_id, self.token, self.breadcrumb
        )
        mock_get_resources.assert_called_once_with(
            [self.resource_id_1, self.resource_id_2],
            self.token,
            self.breadcrumb,
        )

        topic_resources = result["modules"][0]["topics"][0]["resources"]
        self.assertEqual(len(topic_resources), 2)
        self.assertEqual(topic_resources[0]["name"], "HTML Basics")
        self.assertEqual(topic_resources[1]["name"], "CSS Basics")

    @patch("api_utils.services.PathService.get_path")
    @patch("src.services.resource_service.ResourceService.get_resources_by_ids")
    def test_get_path_missing_resources_omitted(
        self, mock_get_resources, mock_parent_get_path
    ):
        raw_path = {
            "_id": self.path_id,
            "name": "Frontend Path",
            "modules": [
                {
                    "name": "Foundations",
                    "topics": [
                        {
                            "name": "HTML & CSS",
                            "resources": [
                                self.resource_id_1,
                                "nonexistent_id",
                            ],
                        }
                    ],
                }
            ],
        }
        resource_summaries = [
            {
                "_id": self.resource_id_1,
                "name": "HTML Basics",
            },
        ]

        mock_parent_get_path.return_value = raw_path
        mock_get_resources.return_value = resource_summaries

        result = PathService.get_path(self.path_id, self.token, self.breadcrumb)

        topic_resources = result["modules"][0]["topics"][0]["resources"]
        self.assertEqual(len(topic_resources), 1)
        self.assertEqual(topic_resources[0]["_id"], self.resource_id_1)

    def test_inherited_methods_exist(self):
        self.assertTrue(hasattr(PathService, "get_paths"))


if __name__ == "__main__":
    unittest.main()
