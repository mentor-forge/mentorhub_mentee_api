"""
Mentee Journey control: clone-on-GET, enrich, PATCH, promote/advance/complete.
"""

import copy
import logging
from bson import ObjectId
from bson.errors import InvalidId

from api_utils import MongoIO, Config
from api_utils.mongo_utils import encode_document
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
from api_utils.services import JourneyService as SharedJourneyService
from api_utils.services.journey_service import TEMPLATE_JOURNEY_ID

logger = logging.getLogger(__name__)

RESTRICTED_UPDATE_FIELDS = [
    "_id",
    "profile_id",
    "created",
    "saved",
    "library",
    "now",
    "next",
    "profile",
]


class JourneyService(SharedJourneyService):
    """Mentee-domain Journey writes and BFF enrich."""

    @classmethod
    def _validate_object_id(cls, value, field_name):
        try:
            ObjectId(value)
        except (InvalidId, TypeError):
            raise HTTPBadRequest(f"{field_name} must be a valid MongoDB ObjectId")

    @classmethod
    def _oid(cls, value):
        return ObjectId(value)

    @classmethod
    def _check_permission(cls, token, operation, journey_id=None):
        if operation == "read":
            if hasattr(super(), "_check_permission"):
                return super()._check_permission(token, operation)
            return
        if operation == "update":
            profile_id = token.get("profile_id") if token else None
            roles = token.get("roles", []) if token else []
            if journey_id == profile_id or "admin" in roles:
                return
            raise HTTPForbidden("Insufficient permissions to update this journey")
        if operation == "mutate":
            if token and token.get("profile_id"):
                return
            raise HTTPForbidden("Insufficient permissions for this journey operation")
        if operation == "complete":
            roles = token.get("roles", []) if token else []
            config = Config.get_instance()
            admin_role = getattr(config, "ROLE_ADMIN", "admin")
            mentee_role = getattr(config, "ROLE_MENTEE", "mentee")
            if (
                admin_role in roles
                or "admin" in roles
                or mentee_role in roles
                or "mentee" in roles
            ):
                return
            raise HTTPForbidden("Mentee role required to complete resources")
        if operation == "create":
            return

    @classmethod
    def _validate_update_data(cls, data):
        for field in RESTRICTED_UPDATE_FIELDS:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")

    @classmethod
    def _clone_template(cls, profile_id, breadcrumb):
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        template = mongo.get_document(
            config.JOURNEY_COLLECTION_NAME, TEMPLATE_JOURNEY_ID
        )
        if template is None:
            raise HTTPNotFound(f"Template journey {TEMPLATE_JOURNEY_ID} not found")

        document = {
            "_id": profile_id,
            "profile_id": profile_id,
            "status": template.get("status", "active"),
            "library": copy.deepcopy(template.get("library", [])),
            "now": copy.deepcopy(template.get("now", [])),
            "next": copy.deepcopy(template.get("next", [])),
            "later": copy.deepcopy(template.get("later", [])),
            "created": breadcrumb,
            "saved": breadcrumb,
        }
        encode_document(document, ["_id", "profile_id"], [])
        mongo.create_document(config.JOURNEY_COLLECTION_NAME, document)
        created = mongo.get_document(config.JOURNEY_COLLECTION_NAME, profile_id)
        logger.info(f"Created journey {profile_id} from template for user {profile_id}")
        return created

    @classmethod
    def get_my_journey(cls, token, breadcrumb):
        try:
            cls._check_permission(token, "read")
            profile_id = token.get("profile_id") if token else None
            if not profile_id:
                raise HTTPBadRequest("profile_id is required on token")
            try:
                journey = cls.get_journey(profile_id, token, breadcrumb)
                logger.info(
                    f"Retrieved journey {profile_id} for user {token.get('user_id')}"
                )
                return journey
            except HTTPNotFound:
                return cls._clone_template(profile_id, breadcrumb)
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving journey for profile {token.get('profile_id')}: {e}"
            )
            raise HTTPInternalServerError("Failed to retrieve journey")

    @classmethod
    def get_my_journey_detail(cls, token, breadcrumb):
        try:
            profile_id = token.get("profile_id") if token else None
            if not profile_id:
                raise HTTPBadRequest("profile_id is required on token")

            journey = cls.get_my_journey(token, breadcrumb)

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            profile = mongo.get_document(config.PROFILE_COLLECTION_NAME, profile_id)
            if profile is None:
                raise HTTPNotFound(f"Profile {profile_id} not found")

            logger.info(
                f"Retrieved journey detail with profile {profile_id} "
                f"for user {token.get('user_id')}"
            )
            return {**journey, "profile": profile}
        except (HTTPBadRequest, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving journey detail for profile {token.get('profile_id')}: {e}"
            )
            raise HTTPInternalServerError("Failed to retrieve journey detail")

    @classmethod
    def create_journey(cls, data, token, breadcrumb):
        try:
            cls._check_permission(token, "create")
            if "_id" in data:
                del data["_id"]
            data["created"] = breadcrumb
            data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            journey_id = mongo.create_document(config.JOURNEY_COLLECTION_NAME, data)
            logger.info(f"Created journey {journey_id} for user {token.get('user_id')}")
            return journey_id
        except HTTPForbidden:
            raise
        except Exception as e:
            logger.error(f"Error creating journey: {e}")
            raise HTTPInternalServerError(f"Failed to create journey: {e}")

    @classmethod
    def update_journey(cls, journey_id, data, token, breadcrumb):
        try:
            cls._check_permission(token, "update", journey_id=journey_id)
            cls._validate_update_data(data)

            set_data = {
                k: v for k, v in data.items() if k not in RESTRICTED_UPDATE_FIELDS
            }
            set_data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.JOURNEY_COLLECTION_NAME,
                document_id=journey_id,
                set_data=set_data,
            )
            if updated is None:
                raise HTTPNotFound(f"Journey {journey_id} not found")

            logger.info(f"Updated journey {journey_id} for user {token.get('user_id')}")
            return updated
        except (HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error updating journey {journey_id}: {e}")
            raise HTTPInternalServerError(f"Failed to update journey {journey_id}")

    @classmethod
    def _resource_id_in_next(cls, next_modules, resource_id):
        target = cls._oid(resource_id)
        for module in next_modules:
            for topic in module.get("topics", []):
                for rid in topic.get("resources", []):
                    if cls._oid(rid) == target:
                        return True
        return False

    @classmethod
    def _remove_resource_from_next(cls, next_modules, resource_id):
        target = cls._oid(resource_id)
        found = False
        new_modules = []
        for module in next_modules:
            new_topics = []
            for topic in module.get("topics", []):
                resources = topic.get("resources", [])
                kept = [r for r in resources if cls._oid(r) != target]
                if len(kept) != len(resources):
                    found = True
                if kept:
                    topic_copy = copy.deepcopy(topic)
                    topic_copy["resources"] = kept
                    new_topics.append(topic_copy)
            if new_topics:
                module_copy = copy.deepcopy(module)
                module_copy["topics"] = new_topics
                new_modules.append(module_copy)
        return found, new_modules

    @classmethod
    def _find_now_entry(cls, now_items, resource):
        resource_oid = cls._oid(resource["_id"])
        for index, item in enumerate(now_items):
            rid = item.get("resource_id")
            if rid is not None and cls._oid(rid) == resource_oid:
                return index, item
        return None, None

    @classmethod
    def _event_token(cls, token, resource_id, journey_id):
        event_token = dict(token) if token else {}
        event_token["resource_id"] = resource_id
        event_token["journey_id"] = journey_id
        return event_token

    @classmethod
    def advance_resource(cls, resource_id, token, breadcrumb):
        try:
            cls._check_permission(token, "mutate")
            cls._validate_object_id(resource_id, "resource_id")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            resource = mongo.get_document(config.RESOURCE_COLLECTION_NAME, resource_id)
            if resource is None:
                raise HTTPNotFound(f"Resource {resource_id} not found")

            journey = cls.get_my_journey(token, breadcrumb)
            journey_id = str(journey["_id"])
            next_modules = journey.get("next", [])

            if not cls._resource_id_in_next(next_modules, resource_id):
                raise HTTPNotFound(
                    f"Resource {resource_id} not found in journey next scope"
                )

            found, updated_next = cls._remove_resource_from_next(
                next_modules, resource_id
            )
            if not found:
                raise HTTPNotFound(
                    f"Resource {resource_id} not found in journey next scope"
                )

            now_item = {
                "resource_id": resource_id,
                "added": breadcrumb["at_time"],
                "used": 0,
            }
            now_items = copy.deepcopy(journey.get("now", []))
            now_items.append(now_item)

            set_data = {
                "next": updated_next,
                "now": now_items,
                "saved": breadcrumb,
            }
            encode_document(
                set_data, ["resources", "resource_id"], ["added", "started"]
            )
            updated = mongo.update_document(
                config.JOURNEY_COLLECTION_NAME,
                document_id=journey_id,
                set_data=set_data,
            )

            from src.services.event_service import EventService

            EventService.create_event(
                {"type": config.EVENT_TYPE_ADVANCED},
                cls._event_token(token, resource_id, journey_id),
                breadcrumb,
            )

            logger.info(f"Advanced resource {resource_id} for journey {journey_id}")
            return updated
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error advancing resource {resource_id}: {e}")
            raise HTTPInternalServerError(f"Failed to advance resource {resource_id}")

    @classmethod
    def complete_resource(cls, resource_id, data, token, breadcrumb):
        try:
            cls._check_permission(token, "complete")
            cls._validate_object_id(resource_id, "resource_id")
            data = data or {}

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            resource = mongo.get_document(config.RESOURCE_COLLECTION_NAME, resource_id)
            if resource is None:
                raise HTTPNotFound(f"Resource {resource_id} not found")

            journey = cls.get_my_journey(token, breadcrumb)
            journey_id = str(journey["_id"])
            now_items = copy.deepcopy(journey.get("now", []))

            index, now_entry = cls._find_now_entry(now_items, resource)
            if index is None:
                raise HTTPNotFound(
                    f"Resource {resource_id} not found in journey now scope"
                )

            now_items.pop(index)
            library_item = {
                "resource_id": resource_id,
                "started": now_entry.get("started") or breadcrumb["at_time"],
                "completed": breadcrumb["at_time"],
                "used": now_entry.get("used", 0),
            }
            rating = data.get("rating")
            if rating is not None:
                library_item["rating"] = rating

            library_items = copy.deepcopy(journey.get("library", []))
            library_items.append(library_item)

            set_data = {
                "now": now_items,
                "library": library_items,
                "saved": breadcrumb,
            }
            encode_document(
                set_data, ["resource_id"], ["added", "started", "completed"]
            )
            updated = mongo.update_document(
                config.JOURNEY_COLLECTION_NAME,
                document_id=journey_id,
                set_data=set_data,
            )

            from src.services.aggregation_service import AggregationService
            from src.services.event_service import EventService

            AggregationService.add_completion(
                resource_id,
                rating,
                data.get("note"),
                data.get("duration"),
                token,
                breadcrumb,
            )
            EventService.create_event(
                {"type": config.EVENT_TYPE_COMPLETED},
                cls._event_token(token, resource_id, journey_id),
                breadcrumb,
            )

            logger.info(f"Completed resource {resource_id} for journey {journey_id}")
            return updated
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error completing resource {resource_id}: {e}")
            raise HTTPInternalServerError(f"Failed to complete resource {resource_id}")

    @classmethod
    def _path_id_in_later(cls, later_items, path_id):
        target = cls._oid(path_id)
        return any(cls._oid(item) == target for item in later_items)

    @classmethod
    def _module_to_next_module(cls, module):
        next_module = {
            "name": module.get("name"),
            "description": module.get("description"),
            "topics": [],
        }
        for topic in module.get("topics", []):
            next_module["topics"].append(
                {
                    "name": topic.get("name"),
                    "description": topic.get("description"),
                    "resources": list(topic.get("resources", [])),
                }
            )
        return next_module

    @classmethod
    def _module_name_in_next(cls, next_modules, module_name):
        return any(module.get("name") == module_name for module in next_modules)

    @classmethod
    def _load_path_and_journey(cls, path_id, token, breadcrumb):
        cls._check_permission(token, "mutate")
        cls._validate_object_id(path_id, "path_id")

        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        path = mongo.get_document(config.PATH_COLLECTION_NAME, path_id)
        if path is None:
            raise HTTPNotFound(f"Path {path_id} not found")

        journey = cls.get_my_journey(token, breadcrumb)
        journey_id = str(journey["_id"])
        later_items = journey.get("later", [])

        if not cls._path_id_in_later(later_items, path_id):
            raise HTTPNotFound(f"Path {path_id} not found in journey later scope")

        return mongo, config, path, journey, journey_id, later_items

    @classmethod
    def promote_path_to_next(cls, path_id, token, breadcrumb):
        try:
            mongo, config, path, journey, journey_id, later_items = (
                cls._load_path_and_journey(path_id, token, breadcrumb)
            )

            path_modules = path.get("modules", [])
            if not path_modules:
                raise HTTPBadRequest(f"Path {path_id} has no modules to promote")

            next_modules = copy.deepcopy(journey.get("next", []))
            for module in path_modules:
                next_modules.append(cls._module_to_next_module(module))

            target_path_oid = cls._oid(path_id)
            updated_later = [
                item for item in later_items if cls._oid(item) != target_path_oid
            ]

            set_data = {
                "next": next_modules,
                "later": updated_later,
                "saved": breadcrumb,
            }
            encode_document(set_data, ["resources", "later"], [])
            updated = mongo.update_document(
                config.JOURNEY_COLLECTION_NAME,
                document_id=journey_id,
                set_data=set_data,
            )

            logger.info(f"Promoted path {path_id} to next for journey {journey_id}")
            return updated
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error promoting path {path_id} to next: {e}")
            raise HTTPInternalServerError(f"Failed to promote path {path_id} to next")

    @classmethod
    def promote_module_to_next(cls, path_id, module_name, token, breadcrumb):
        try:
            mongo, config, path, journey, journey_id, _later_items = (
                cls._load_path_and_journey(path_id, token, breadcrumb)
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
            if cls._module_name_in_next(next_modules, module_name):
                raise HTTPBadRequest(
                    f"Module {module_name!r} is already present in journey next scope"
                )

            next_modules.append(cls._module_to_next_module(path_module))

            set_data = {
                "next": next_modules,
                "saved": breadcrumb,
            }
            encode_document(set_data, ["resources"], [])
            updated = mongo.update_document(
                config.JOURNEY_COLLECTION_NAME,
                document_id=journey_id,
                set_data=set_data,
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
