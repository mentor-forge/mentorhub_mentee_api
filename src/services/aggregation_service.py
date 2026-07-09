"""
Aggregation service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Resource_Aggregation domain.
"""

import logging
import re
from datetime import timedelta

from bson import ObjectId
from bson.errors import InvalidId
from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPInternalServerError,
)

logger = logging.getLogger(__name__)

ZERO_DURATION = "PT0S"
_DURATION_PATTERN = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+(?:\.\d+)?)S)?$"
)


class AggregationService:
    """
    Service class for Resource_Aggregation domain operations.
    """

    @staticmethod
    def _resource_object_id(resource_id):
        try:
            return ObjectId(resource_id)
        except (InvalidId, TypeError):
            raise HTTPBadRequest("resource_id must be a valid MongoDB ObjectId")

    @staticmethod
    def _parse_duration(value):
        if not value:
            return timedelta(0)
        if isinstance(value, timedelta):
            return value
        match = _DURATION_PATTERN.match(str(value))
        if not match:
            return timedelta(0)
        hours = int(match.group("hours") or 0)
        minutes = int(match.group("minutes") or 0)
        seconds = float(match.group("seconds") or 0)
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)

    @staticmethod
    def _format_duration(delta):
        if delta.total_seconds() <= 0:
            return ZERO_DURATION
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = ["PT"]
        if hours:
            parts.append(f"{hours}H")
        if minutes:
            parts.append(f"{minutes}M")
        if seconds or not (hours or minutes):
            parts.append(f"{seconds}S")
        return "".join(parts)

    @staticmethod
    def _add_durations(current, addition):
        return AggregationService._format_duration(
            AggregationService._parse_duration(current)
            + AggregationService._parse_duration(addition)
        )

    @staticmethod
    def _check_permission(token, operation):
        if operation == "add_completion":
            config = Config.get_instance()
            mentee_role = getattr(config, "ROLE_MENTEE", "mentee")
            if mentee_role not in token.get("roles", []):
                raise HTTPForbidden("Mentee role required to record completions")

    @staticmethod
    def _find_aggregation(mongo, collection_name, resource_object_id):
        aggregation = mongo.get_document(collection_name, str(resource_object_id))
        if aggregation is not None:
            return aggregation

        legacy_matches = mongo.get_documents(
            collection_name, match={"resource_id": resource_object_id}
        )
        return legacy_matches[0] if legacy_matches else None

    @staticmethod
    def _new_aggregation_document(resource_object_id, breadcrumb):
        return {
            "_id": resource_object_id,
            "note_count": 0,
            "completions": 0,
            "hits": 0,
            "rating_count": 0,
            "rating_sum": 0,
            "duration": ZERO_DURATION,
            "created": breadcrumb,
            "last_saved": breadcrumb,
        }

    @staticmethod
    def _get_or_create_aggregation(resource_id, token, breadcrumb):
        AggregationService._check_permission(token, "read")
        resource_object_id = AggregationService._resource_object_id(resource_id)

        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        collection_name = config.RESOURCE_AGGREGATION_COLLECTION_NAME
        aggregation = AggregationService._find_aggregation(
            mongo, collection_name, resource_object_id
        )
        if aggregation is not None:
            return aggregation

        document = AggregationService._new_aggregation_document(
            resource_object_id, breadcrumb
        )
        mongo.create_document(collection_name, document)
        created = mongo.get_document(collection_name, str(resource_object_id))
        logger.info(
            f"Created aggregation for resource {resource_id} "
            f"for user {token.get('user_id')}"
        )
        return created

    @staticmethod
    def get_aggregation_for_resource(resource_id, token, breadcrumb):
        """
        Retrieve aggregation metrics for a resource.

        Returns:
            dict or None: The aggregation document, or None if none exists
        """
        try:
            AggregationService._check_permission(token, "read")
            resource_object_id = AggregationService._resource_object_id(resource_id)

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            aggregation = AggregationService._find_aggregation(
                mongo, config.RESOURCE_AGGREGATION_COLLECTION_NAME, resource_object_id
            )

            logger.info(
                f"Retrieved aggregation for resource {resource_id} "
                f"for user {token.get('user_id')}"
            )
            return aggregation
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving aggregation for resource {resource_id}: {str(e)}"
            )
            raise HTTPInternalServerError(
                f"Failed to retrieve aggregation for resource {resource_id}"
            )

    @staticmethod
    def get_aggregation_detail(resource_id, token, breadcrumb):
        """
        Retrieve or create aggregation metrics and related notes for a resource.

        Returns:
            dict: {aggregation, notes}
        """
        try:
            aggregation = AggregationService._get_or_create_aggregation(
                resource_id, token, breadcrumb
            )

            from src.services.note_service import NoteService

            notes = NoteService.get_notes_for_resource(resource_id, token, breadcrumb)

            logger.info(
                f"Retrieved aggregation detail for resource {resource_id} "
                f"for user {token.get('user_id')}"
            )
            return {"aggregation": aggregation, "notes": notes}
        except (HTTPBadRequest, HTTPForbidden):
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving aggregation detail for resource {resource_id}: {str(e)}"
            )
            raise HTTPInternalServerError(
                f"Failed to retrieve aggregation detail for resource {resource_id}"
            )

    @staticmethod
    def add_completion(resource_id, rating, note, duration, token, breadcrumb):
        """
        Record a resource completion with optional note and duration.

        Requires mentee role.
        """
        try:
            AggregationService._check_permission(token, "add_completion")
            aggregation = AggregationService._get_or_create_aggregation(
                resource_id, token, breadcrumb
            )

            note_count_delta = 0
            if note:
                from src.services.note_service import NoteService

                note_data = {"resource_id": resource_id, "note": note}
                NoteService.create_note(note_data, token, breadcrumb)
                note_count_delta = 1

            set_data = {
                "completions": aggregation.get("completions", 0) + 1,
                "rating_count": aggregation.get("rating_count", 0) + 1,
                "rating_sum": aggregation.get("rating_sum", 0) + rating,
                "note_count": aggregation.get("note_count", 0) + note_count_delta,
                "duration": AggregationService._add_durations(
                    aggregation.get("duration", ZERO_DURATION), duration
                ),
                "last_saved": breadcrumb,
            }

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.RESOURCE_AGGREGATION_COLLECTION_NAME,
                document_id=str(aggregation["_id"]),
                set_data=set_data,
            )

            logger.info(
                f"Recorded completion for resource {resource_id} "
                f"for user {token.get('user_id')}"
            )
            return updated
        except (HTTPBadRequest, HTTPForbidden):
            raise
        except Exception as e:
            logger.error(
                f"Error recording completion for resource {resource_id}: {str(e)}"
            )
            raise HTTPInternalServerError(
                f"Failed to record completion for resource {resource_id}"
            )

    @staticmethod
    def add_hit(resource_id, token, breadcrumb):
        """
        Increment hit count for a resource aggregation.

        Any authenticated user may record a hit.
        """
        try:
            AggregationService._check_permission(token, "add_hit")
            aggregation = AggregationService._get_or_create_aggregation(
                resource_id, token, breadcrumb
            )

            set_data = {
                "hits": aggregation.get("hits", 0) + 1,
                "last_saved": breadcrumb,
            }

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            updated = mongo.update_document(
                config.RESOURCE_AGGREGATION_COLLECTION_NAME,
                document_id=str(aggregation["_id"]),
                set_data=set_data,
            )

            logger.info(
                f"Recorded hit for resource {resource_id} "
                f"for user {token.get('user_id')}"
            )
            return updated
        except (HTTPBadRequest, HTTPForbidden):
            raise
        except Exception as e:
            logger.error(f"Error recording hit for resource {resource_id}: {str(e)}")
            raise HTTPInternalServerError(
                f"Failed to record hit for resource {resource_id}"
            )
