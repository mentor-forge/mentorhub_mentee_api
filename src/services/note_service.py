"""
Note service for business logic and RBAC.

Handles Mentee Note control (inbound create). List/read stay on the parent.
"""

from bson import ObjectId
import logging

from api_utils import MongoIO, Config
from api_utils.mongo_utils import encode_document
from api_utils.flask_utils.exceptions import (
    HTTPForbidden,
    HTTPInternalServerError,
)
from api_utils.services import NoteService as SharedNoteService

logger = logging.getLogger(__name__)

ID_PROPERTIES = ["_id", "resource_id", "profile_id"]
DATE_PROPERTIES = []


class NoteService(SharedNoteService):
    """Mentee Note control: inbound create. List/read stay on the parent."""

    @classmethod
    def _check_permission(cls, token, operation):
        """
        Check permission for Note operations.
        Inbound create requires mentee role (or admin).
        Read operations pass through to parent (outbound filters apply).
        """
        if operation == "create":
            roles = token.get("roles", []) if token else []
            config = Config.get_instance()
            admin_role = getattr(config, "ROLE_ADMIN", "admin")
            mentee_role = getattr(config, "ROLE_MENTEE", "mentee")
            if (
                admin_role not in roles
                and "admin" not in roles
                and mentee_role not in roles
                and "mentee" not in roles
            ):
                raise HTTPForbidden("Note creation requires mentee role")
        else:
            super()._check_permission(token, operation)

    @classmethod
    def create_note(cls, data, token, breadcrumb):
        """
        Create a new Note document.
        Requires mentee or admin role. profile_id must match token.profile_id for non-admin.
        """
        try:
            cls._check_permission(token, "create")

            roles = token.get("roles", []) if token else []
            config = Config.get_instance()
            admin_role = getattr(config, "ROLE_ADMIN", "admin")
            is_admin = admin_role in roles or "admin" in roles

            token_profile_id = token.get("profile_id")
            if not is_admin:
                if not token_profile_id:
                    raise HTTPForbidden("Operation requires profile_id in token")
                if "profile_id" in data and str(data["profile_id"]) != str(
                    token_profile_id
                ):
                    raise HTTPForbidden("Cannot create note for another profile")
                data["profile_id"] = str(token_profile_id)
            elif "profile_id" not in data and token_profile_id:
                data["profile_id"] = str(token_profile_id)

            if "_id" in data:
                del data["_id"]

            encode_document(data, ID_PROPERTIES, DATE_PROPERTIES)

            data["created"] = breadcrumb
            data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            note_id = mongo.create_document(config.NOTE_COLLECTION_NAME, data)
            if "_id" not in data:
                data["_id"] = ObjectId(note_id)
            logger.info(f"Created note {note_id} for user {token.get('user_id')}")
            return data
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating note: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create note: {error_msg}")
