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
_ISO_DURATION_PATTERN = re.compile(
    r"^P(?:(\d+)Y)?(?:(\d+)M)?(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$"
)


class AggregationService:
    """
    Service class for Resource_Aggregation domain operations.
    """

    @staticmethod
    def _check_permission(token, operation):
        if operation == "add_completion":
            roles = token.get("roles", [])
            if Config.get_instance().ROLE_MENTEE in roles:
                return
            raise HTTPForbidden("Mentee role required to record completion")
        if operation == "add_hit":
            return

    @staticmethod
    def _parse_iso_duration(duration_str):
        if not duration_str or duration_str == ZERO_DURATION:
            return timedelta(0)
        match = _ISO_DURATION_PATTERN.match(duration_str)
        if not match:
            raise HTTPBadRequest("duration must be a valid ISO 8601 duration")
        years, months, weeks, days, hours, minutes, seconds = match.groups()
        total_seconds = 0.0
        if years:
            total_seconds += int(years) * 365 * 24 * 3600
        if months:
            total_seconds += int(months) * 30 * 24 * 3600
        if weeks:
            total_seconds += int(weeks) * 7 * 24 * 3600
        if days:
            total_seconds += int(days) * 24 * 3600
        if hours:
            total_seconds += int(hours) * 3600
        if minutes:
            total_seconds += int(minutes) * 60
        if seconds:
            total_seconds += float(seconds)
        return timedelta(seconds=total_seconds)

    @staticmethod
    def _format_iso_duration(delta):
        total_seconds = int(delta.total_seconds())
        if total_seconds <= 0:
            return ZERO_DURATION
        hours, rem = divmod(total_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        parts = "PT"
        if hours:
            parts += f"{hours}H"
        if minutes:
            parts += f"{minutes}M"
        if seconds or parts == "PT":
            parts += f"{seconds}S"
        return parts

    @staticmethod
    def _add_durations(existing, addition):
        total = AggregationService._parse_iso_duration(
            existing or ZERO_DURATION
        ) + AggregationService._parse_iso_duration(addition or ZERO_DURATION)
        return AggregationService._format_iso_duration(total)

    @staticmethod
    def _resource_object_id(resource_id):
        try:
            return ObjectId(resource_id)
        except (InvalidId, TypeError):
            raise HTTPBadRequest("resource_id must be a valid MongoDB ObjectId")

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
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(
                f"Error retrieving aggregation detail for resource {resource_id}: {str(e)}"
            )
            raise HTTPInternalServerError(
                f"Failed to retrieve aggregation detail for resource {resource_id}"
            )

    @staticmethod
    def add_hit(resource_id, token, breadcrumb):
        """
        Increment hit count for a resource aggregation.

        Any authenticated user may record a hit.
        """
        try:
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
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(f"Error recording hit for resource {resource_id}: {str(e)}")
            raise HTTPInternalServerError(
                f"Failed to record hit for resource {resource_id}"
            )

    @staticmethod
    def add_completion(resource_id, rating, note, duration, token, breadcrumb):
        """
        Increment completion counters for a resource aggregation.

        Mentee role required. Does not create Event documents.
        """
        try:
            AggregationService._check_permission(token, "add_completion")
            aggregation = AggregationService._get_or_create_aggregation(
                resource_id, token, breadcrumb
            )

            completions = aggregation.get("completions", 0) + 1
            rating_count = aggregation.get("rating_count", 0)
            rating_sum = aggregation.get("rating_sum", 0)
            note_count = aggregation.get("note_count", 0)

            if rating is not None:
                rating_count += 1
                rating_sum += rating

            if note:
                from src.services.note_service import NoteService

                NoteService.create_note(
                    {
                        "resource_id": resource_id,
                        "profile_id": token.get("profile_id"),
                        "note": note,
                        "status": "active",
                    },
                    token,
                    breadcrumb,
                )
                note_count += 1

            set_data = {
                "completions": completions,
                "rating_count": rating_count,
                "rating_sum": rating_sum,
                "note_count": note_count,
                "duration": AggregationService._add_durations(
                    aggregation.get("duration"), duration
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
