"""
Unit tests for local EventService subclass.
"""

import unittest
from unittest.mock import MagicMock, patch
from src.services.event_service import EventService


class TestEventService(unittest.TestCase):
    """Test cases for EventService subclass."""

    def setUp(self):
        self.breadcrumb = {
            "by_user": "user1",
            "at_time": "2024-01-01T00:00:00Z",
            "from_ip": "127.0.0.1",
            "correlation_id": "corr-1",
        }
        self.resource_id = "507f1f77bcf86cd799439012"
        self.token_with_resource = {
            "user_id": "user1",
            "profile_id": "507f1f77bcf86cd799439011",
            "resource_id": self.resource_id,
            "roles": ["mentee"],
        }
        self.token_without_resource = {
            "user_id": "user1",
            "profile_id": "507f1f77bcf86cd799439011",
            "roles": ["mentee"],
        }

    @patch("src.services.event_service.Config")
    @patch("api_utils.services.EventService.create_event")
    @patch("src.services.aggregation_service.AggregationService.add_hit")
    def test_create_event_link_with_resource_id_triggers_hit(
        self, mock_add_hit, mock_parent_create, mock_config
    ):
        mock_cfg = MagicMock()
        mock_cfg.EVENT_TYPE_LINK = "link"
        mock_config.get_instance.return_value = mock_cfg

        mock_parent_create.return_value = {
            "_id": "event1",
            "type": "link",
            "created": self.breadcrumb,
        }

        data = {"type": "link"}
        result = EventService.create_event(
            data, self.token_with_resource, self.breadcrumb
        )

        self.assertEqual(result["_id"], "event1")
        mock_parent_create.assert_called_once_with(
            data, self.token_with_resource, self.breadcrumb
        )
        mock_add_hit.assert_called_once_with(
            self.resource_id, self.token_with_resource, self.breadcrumb
        )

    @patch("src.services.event_service.Config")
    @patch("api_utils.services.EventService.create_event")
    @patch("src.services.aggregation_service.AggregationService.add_hit")
    def test_create_event_link_without_resource_id_skips_hit(
        self, mock_add_hit, mock_parent_create, mock_config
    ):
        mock_cfg = MagicMock()
        mock_cfg.EVENT_TYPE_LINK = "link"
        mock_config.get_instance.return_value = mock_cfg

        mock_parent_create.return_value = {
            "_id": "event2",
            "type": "link",
            "created": self.breadcrumb,
        }

        data = {"type": "link"}
        result = EventService.create_event(
            data, self.token_without_resource, self.breadcrumb
        )

        self.assertEqual(result["_id"], "event2")
        mock_parent_create.assert_called_once_with(
            data, self.token_without_resource, self.breadcrumb
        )
        mock_add_hit.assert_not_called()

    @patch("src.services.event_service.Config")
    @patch("api_utils.services.EventService.create_event")
    @patch("src.services.aggregation_service.AggregationService.add_hit")
    def test_create_event_non_link_skips_hit(
        self, mock_add_hit, mock_parent_create, mock_config
    ):
        mock_cfg = MagicMock()
        mock_cfg.EVENT_TYPE_LINK = "link"
        mock_config.get_instance.return_value = mock_cfg

        mock_parent_create.return_value = {
            "_id": "event3",
            "type": "advanced",
            "created": self.breadcrumb,
        }

        data = {"type": "advanced"}
        result = EventService.create_event(
            data, self.token_with_resource, self.breadcrumb
        )

        self.assertEqual(result["_id"], "event3")
        mock_parent_create.assert_called_once_with(
            data, self.token_with_resource, self.breadcrumb
        )
        mock_add_hit.assert_not_called()

    def test_inherited_methods_exist(self):
        self.assertTrue(hasattr(EventService, "get_events"))


if __name__ == "__main__":
    unittest.main()
