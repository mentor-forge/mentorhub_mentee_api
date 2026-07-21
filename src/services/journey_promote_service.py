"""
Local Journey promote mutations (later → next).

Temporary implementation in this API repo until harvested into api_utils.services.journey_service.
See tasks/ISSUE.mentorhub_api_utils.harvest_journey_promote_mutations.md.
"""

import copy
import logging

from bson import ObjectId
from bson.errors import InvalidId

from api_utils import MongoIO, Config
from api_utils.services import JourneyService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)

logger = logging.getLogger(__name__)


class JourneyPromoteService:
    """Promote Path content from journey.later into journey.next."""

    @staticmethod
    def _check_mutate_permission(token):
        if token.get("profile_id"):
            return
        raise HTTPForbidden("Insufficient permissions for this journey operation")

    @staticmethod
    def _validate_object_id(value, field_name):
        try:
            ObjectId(value)
        except (InvalidId, TypeError):
            raise HTTPBadRequest(f"{field_name} must be a valid MongoDB ObjectId")

    @staticmethod
    def _normalize_id(value):
        if isinstance(value, ObjectId):
            return str(value)
        return str(value)

    @staticmethod
    def _path_id_in_later(later_items, path_id):
        target = JourneyPromoteService._normalize_id(path_id)
        return any(
            JourneyPromoteService._normalize_id(item) == target for item in later_items
        )

    @staticmethod
    def _module_to_next_module(module):
        next_module = {
            "name": module.get("name"),
            "description": module.get("description"),
            "topics": [],
        }
        for topic in module.get("topics", []):
            resources = [
                JourneyPromoteService._normalize_id(resource_id)
                for resource_id in topic.get("resources", [])
            ]
            next_module["topics"].append(
                {
                    "name": topic.get("name"),
                    "description": topic.get("description"),
                    "resources": resources,
                }
            )
        return next_module

    @staticmethod
    def _module_name_in_next(next_modules, module_name):
        return any(module.get("name") == module_name for module in next_modules)

    @staticmethod
    def _load_path_and_journey(path_id, token, breadcrumb):
        JourneyPromoteService._check_mutate_permission(token)
        JourneyPromoteService._validate_object_id(path_id, "path_id")

        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        path = mongo.get_document(config.PATH_COLLECTION_NAME, path_id)
        if path is None:
            raise HTTPNotFound(f"Path {path_id} not found")

        journey = JourneyService.get_my_journey(token, breadcrumb)
        journey_id = JourneyPromoteService._normalize_id(journey["_id"])
        later_items = journey.get("later", [])

        if not JourneyPromoteService._path_id_in_later(later_items, path_id):
            raise HTTPNotFound(f"Path {path_id} not found in journey later scope")

        return mongo, config, path, journey, journey_id, later_items

    @staticmethod
    def promote_path_to_next(path_id, token, breadcrumb):
        try:
            mongo, config, path, journey, journey_id, later_items = (
                JourneyPromoteService._load_path_and_journey(path_id, token, breadcrumb)
            )

            path_modules = path.get("modules", [])
            if not path_modules:
                raise HTTPBadRequest(f"Path {path_id} has no modules to promote")

            next_modules = copy.deepcopy(journey.get("next", []))
            for module in path_modules:
                next_modules.append(
                    JourneyPromoteService._module_to_next_module(module)
                )

            normalized_path_id = JourneyPromoteService._normalize_id(path_id)
            updated_later = [
                item
                for item in later_items
                if JourneyPromoteService._normalize_id(item) != normalized_path_id
            ]

            updated = mongo.update_document(
                config.JOURNEY_COLLECTION_NAME,
                document_id=journey_id,
                set_data={
                    "next": next_modules,
                    "later": updated_later,
                    "saved": breadcrumb,
                },
            )

            logger.info(f"Promoted path {path_id} to next for journey {journey_id}")
            return updated
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error promoting path {path_id} to next: {e}")
            raise HTTPInternalServerError(f"Failed to promote path {path_id} to next")

    @staticmethod
    def promote_module_to_next(path_id, module_name, token, breadcrumb):
        try:
            mongo, config, path, journey, journey_id, _later_items = (
                JourneyPromoteService._load_path_and_journey(path_id, token, breadcrumb)
            )

            if not module_name:
                raise HTTPBadRequest("module_name is required")

            path_module = None
            for module in path.get("modules", []):
                if module.get("name") == module_name:
                    path_module = module
                    break

            if path_module is None:
                raise HTTPNotFound(
                    f"Module {module_name!r} not found in path {path_id}"
                )

            next_modules = copy.deepcopy(journey.get("next", []))
            if JourneyPromoteService._module_name_in_next(next_modules, module_name):
                raise HTTPBadRequest(
                    f"Module {module_name!r} is already present in journey next scope"
                )

            next_modules.append(
                JourneyPromoteService._module_to_next_module(path_module)
            )

            updated = mongo.update_document(
                config.JOURNEY_COLLECTION_NAME,
                document_id=journey_id,
                set_data={
                    "next": next_modules,
                    "saved": breadcrumb,
                },
            )

            logger.info(
                f"Promoted module {module_name!r} from path {path_id} "
                f"to next for journey {journey_id}"
            )
            return updated
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(
                f"Error promoting module {module_name!r} from path {path_id} to next: {e}"
            )
            raise HTTPInternalServerError(
                f"Failed to promote module {module_name!r} from path {path_id} to next"
            )
