"""
Journey service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Journey domain.
"""

import copy
import logging

from bson import ObjectId
from bson.errors import InvalidId

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)

logger = logging.getLogger(__name__)

TEMPLATE_JOURNEY_ID = "ffff00000000000000000001"

RESTRICTED_UPDATE_FIELDS = [
    "_id",
    "profile_id",
    "created",
    "saved",
    "library",
    "now",
    "next",
]


class JourneyService:
    """Service class for Journey domain operations."""

    @staticmethod
    def _check_permission(token, operation, journey_id=None):
        if operation == "read":
            return
        if operation == "update":
            profile_id = token.get("profile_id")
            roles = token.get("roles", [])
            if journey_id == profile_id or "admin" in roles:
                return
            raise HTTPForbidden("Insufficient permissions to update this journey")
        if operation == "mutate":
            if token.get("profile_id"):
                return
            raise HTTPForbidden("Insufficient permissions for this journey operation")
        if operation == "complete":
            roles = token.get("roles", [])
            if Config.get_instance().ROLE_MENTEE in roles:
                return
            raise HTTPForbidden("Mentee role required to complete resources")

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
    def _validate_update_data(data):
        for field in RESTRICTED_UPDATE_FIELDS:
            if field in data:
                raise HTTPForbidden(f"Cannot update {field} field")

    @staticmethod
    def _clone_template(profile_id, breadcrumb):
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        template = mongo.get_document(
            config.JOURNEY_COLLECTION_NAME, TEMPLATE_JOURNEY_ID
        )
        if template is None:
            raise HTTPNotFound(f"Template journey {TEMPLATE_JOURNEY_ID} not found")

        document = {
            "_id": ObjectId(profile_id),
            "profile_id": ObjectId(profile_id),
            "status": template.get("status", "active"),
            "library": copy.deepcopy(template.get("library", [])),
            "now": copy.deepcopy(template.get("now", [])),
            "next": copy.deepcopy(template.get("next", [])),
            "later": copy.deepcopy(template.get("later", [])),
            "created": breadcrumb,
            "saved": breadcrumb,
        }
        mongo.create_document(config.JOURNEY_COLLECTION_NAME, document)
        created = mongo.get_document(config.JOURNEY_COLLECTION_NAME, profile_id)
        logger.info(f"Created journey {profile_id} from template for user {profile_id}")
        return created

    @staticmethod
    def get_my_journey(token, breadcrumb):
        try:
            JourneyService._check_permission(token, "read")
            profile_id = token.get("profile_id")
            if not profile_id:
                raise HTTPBadRequest("profile_id is required on token")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            journey = mongo.get_document(config.JOURNEY_COLLECTION_NAME, profile_id)
            if journey is not None:
                logger.info(
                    f"Retrieved journey {profile_id} for user {token.get('user_id')}"
                )
                return journey

            return JourneyService._clone_template(profile_id, breadcrumb)
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error retrieving journey for profile {profile_id}: {e}")
            raise HTTPInternalServerError("Failed to retrieve journey")

    @staticmethod
    def get_journey(journey_id, token, breadcrumb):
        try:
            JourneyService._check_permission(token, "read")
            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            journey = mongo.get_document(config.JOURNEY_COLLECTION_NAME, journey_id)
            if journey is None:
                raise HTTPNotFound(f"Journey {journey_id} not found")
            return journey
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving journey {journey_id}: {e}")
            raise HTTPInternalServerError(f"Failed to retrieve journey {journey_id}")

    @staticmethod
    def create_journey(data, token, breadcrumb):
        try:
            JourneyService._check_permission(token, "create")
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

    @staticmethod
    def update_journey(journey_id, data, token, breadcrumb):
        try:
            JourneyService._check_permission(token, "update", journey_id=journey_id)
            JourneyService._validate_update_data(data)

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

    @staticmethod
    def _resource_id_in_next(next_modules, resource_id):
        target = JourneyService._normalize_id(resource_id)
        for module in next_modules:
            for topic in module.get("topics", []):
                for rid in topic.get("resources", []):
                    if JourneyService._normalize_id(rid) == target:
                        return True
        return False

    @staticmethod
    def _remove_resource_from_next(next_modules, resource_id):
        target = JourneyService._normalize_id(resource_id)
        found = False
        new_modules = []
        for module in next_modules:
            new_topics = []
            for topic in module.get("topics", []):
                resources = topic.get("resources", [])
                kept = [
                    r for r in resources if JourneyService._normalize_id(r) != target
                ]
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

    @staticmethod
    def _find_now_entry(now_items, resource):
        resource_oid = JourneyService._normalize_id(resource["_id"])
        resource_name = resource.get("name")
        for index, item in enumerate(now_items):
            item_rid = JourneyService._normalize_id(item.get("resource_id", ""))
            if item_rid == resource_oid or item.get("resource_id") == resource_name:
                return index, item
        return None, None

    @staticmethod
    def _event_token(token, resource_id, journey_id):
        event_token = dict(token)
        event_token["resource_id"] = resource_id
        event_token["journey_id"] = journey_id
        return event_token

    @staticmethod
    def advance_resource(resource_id, token, breadcrumb):
        try:
            JourneyService._check_permission(token, "mutate")
            JourneyService._validate_object_id(resource_id, "resource_id")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            resource = mongo.get_document(config.RESOURCE_COLLECTION_NAME, resource_id)
            if resource is None:
                raise HTTPNotFound(f"Resource {resource_id} not found")

            journey = JourneyService.get_my_journey(token, breadcrumb)
            journey_id = JourneyService._normalize_id(journey["_id"])
            next_modules = journey.get("next", [])

            if not JourneyService._resource_id_in_next(next_modules, resource_id):
                raise HTTPNotFound(
                    f"Resource {resource_id} not found in journey next scope"
                )

            found, updated_next = JourneyService._remove_resource_from_next(
                next_modules, resource_id
            )
            if not found:
                raise HTTPNotFound(
                    f"Resource {resource_id} not found in journey next scope"
                )

            now_item = {
                "resource_id": resource.get("name", resource_id),
                "added": breadcrumb["at_time"],
                "used": 0,
            }
            now_items = copy.deepcopy(journey.get("now", []))
            now_items.append(now_item)

            updated = mongo.update_document(
                config.JOURNEY_COLLECTION_NAME,
                document_id=journey_id,
                set_data={
                    "next": updated_next,
                    "now": now_items,
                    "saved": breadcrumb,
                },
            )

            from src.services.event_service import EventService

            EventService.create_event(
                {"type": config.EVENT_TYPE_ADVANCED},
                JourneyService._event_token(token, resource_id, journey_id),
                breadcrumb,
            )

            logger.info(f"Advanced resource {resource_id} for journey {journey_id}")
            return updated
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error advancing resource {resource_id}: {e}")
            raise HTTPInternalServerError(f"Failed to advance resource {resource_id}")

    @staticmethod
    def complete_resource(resource_id, data, token, breadcrumb):
        try:
            JourneyService._check_permission(token, "complete")
            JourneyService._validate_object_id(resource_id, "resource_id")
            data = data or {}

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            resource = mongo.get_document(config.RESOURCE_COLLECTION_NAME, resource_id)
            if resource is None:
                raise HTTPNotFound(f"Resource {resource_id} not found")

            journey = JourneyService.get_my_journey(token, breadcrumb)
            journey_id = JourneyService._normalize_id(journey["_id"])
            now_items = copy.deepcopy(journey.get("now", []))

            index, now_entry = JourneyService._find_now_entry(now_items, resource)
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

            updated = mongo.update_document(
                config.JOURNEY_COLLECTION_NAME,
                document_id=journey_id,
                set_data={
                    "now": now_items,
                    "library": library_items,
                    "saved": breadcrumb,
                },
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
                JourneyService._event_token(token, resource_id, journey_id),
                breadcrumb,
            )

            logger.info(f"Completed resource {resource_id} for journey {journey_id}")
            return updated
        except (HTTPBadRequest, HTTPForbidden, HTTPNotFound):
            raise
        except Exception as e:
            logger.error(f"Error completing resource {resource_id}: {e}")
            raise HTTPInternalServerError(f"Failed to complete resource {resource_id}")
