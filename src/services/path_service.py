"""
Path service for business logic and RBAC.

Subclasses shared PathService and enriches nested topic resources.
"""

from api_utils.services import PathService as SharedPathService
from src.services.resource_service import ResourceService


class PathService(SharedPathService):
    """Mentee Path service: enriches nested topic resources."""

    @classmethod
    def _collect_resource_ids(cls, path):
        resource_ids = []
        seen = set()
        for module in path.get("modules") or []:
            for topic in module.get("topics") or []:
                for resource_id in topic.get("resources") or []:
                    resource_key = str(resource_id)
                    if resource_key not in seen:
                        seen.add(resource_key)
                        resource_ids.append(resource_key)
        return resource_ids

    @classmethod
    def _enrich_path_resources(cls, path, resource_summaries):
        summary_by_id = {str(summary["_id"]): summary for summary in resource_summaries}
        enriched = dict(path)
        modules = []
        for module in path.get("modules") or []:
            enriched_module = dict(module)
            topics = []
            for topic in module.get("topics") or []:
                enriched_topic = dict(topic)
                enriched_resources = []
                for resource_id in topic.get("resources") or []:
                    summary = summary_by_id.get(str(resource_id))
                    if summary is not None:
                        enriched_resources.append(summary)
                enriched_topic["resources"] = enriched_resources
                topics.append(enriched_topic)
            enriched_module["topics"] = topics
            modules.append(enriched_module)
        enriched["modules"] = modules
        return enriched

    @classmethod
    def get_path(cls, path_id, token, breadcrumb):
        """
        Retrieve a specific path document by ID with enriched resource summaries.
        """
        path = super().get_path(path_id, token, breadcrumb)
        resource_ids = cls._collect_resource_ids(path)
        resource_summaries = ResourceService.get_resources_by_ids(
            resource_ids, token, breadcrumb
        )
        return cls._enrich_path_resources(path, resource_summaries)
