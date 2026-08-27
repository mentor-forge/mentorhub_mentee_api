"""
Resource service for business logic and RBAC.

Subclasses shared ResourceService and provides composite get_resource (resource + aggregation + notes).
"""

from api_utils.services import ResourceService as SharedResourceService
from src.services.aggregation_service import AggregationService
from src.services.note_service import NoteService


class ResourceService(SharedResourceService):
    """Mentee Resource service: composite get_resource (BFF detail)."""

    @classmethod
    def get_resource(cls, resource_id, token, breadcrumb):
        """
        Retrieve Resource detail composite: resource document, aggregation metrics, and notes.
        """
        resource = super().get_resource(resource_id, token, breadcrumb)
        aggregation = AggregationService.get_aggregation_for_resource(
            resource_id, token, breadcrumb
        )
        notes = NoteService.list_all_notes_for_resource(resource_id, token, breadcrumb)
        return {
            "resource": resource,
            "aggregation": aggregation,
            "notes": notes,
        }
