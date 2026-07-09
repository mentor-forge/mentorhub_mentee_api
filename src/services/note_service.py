"""
Note service for business logic and RBAC.

Handles RBAC checks and MongoDB operations for Note domain.
"""

from api_utils import MongoIO, Config
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPForbidden,
    HTTPNotFound,
    HTTPInternalServerError,
)
import logging

logger = logging.getLogger(__name__)


class NoteService:
    """
    Service class for Note domain operations.
    """

    @staticmethod
    def _check_permission(token, operation):
        """Any authenticated user may create and read notes."""
        pass

    @staticmethod
    def create_note(data, token, breadcrumb):
        """
        Create a new note document.

        Args:
            data: Dictionary containing note data
            token: Token dictionary with user_id and roles
            breadcrumb: Breadcrumb dictionary for logging

        Returns:
            str: The ID of the created note document
        """
        try:
            NoteService._check_permission(token, "create")

            if "_id" in data:
                del data["_id"]

            data["created"] = breadcrumb
            data["saved"] = breadcrumb

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            note_id = mongo.create_document(config.NOTE_COLLECTION_NAME, data)
            logger.info(f"Created note { note_id} for user {token.get('user_id')}")
            return note_id
        except HTTPForbidden:
            raise
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creating note: {error_msg}")
            raise HTTPInternalServerError(f"Failed to create note: {error_msg}")

    @staticmethod
    def get_notes_for_resource(resource_id, token, breadcrumb):
        """
        Retrieve all notes for a resource.

        Args:
            resource_id: The resource ID to look up
            token: Authentication token
            breadcrumb: Audit breadcrumb

        Returns:
            list: Note documents for the resource
        """
        try:
            NoteService._check_permission(token, "read")

            from bson import ObjectId
            from bson.errors import InvalidId

            try:
                resource_object_id = ObjectId(resource_id)
            except (InvalidId, TypeError):
                raise HTTPBadRequest("resource_id must be a valid MongoDB ObjectId")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            collection = mongo.get_collection(config.NOTE_COLLECTION_NAME)
            notes = list(
                collection.find({"resource_id": resource_object_id}).sort(
                    "created.at_time", -1
                )
            )

            logger.info(
                f"Retrieved {len(notes)} notes for resource {resource_id} "
                f"for user {token.get('user_id')}"
            )
            return notes
        except HTTPBadRequest:
            raise
        except Exception as e:
            logger.error(f"Error retrieving notes for resource {resource_id}: {str(e)}")
            raise HTTPInternalServerError(
                f"Failed to retrieve notes for resource {resource_id}"
            )

    @staticmethod
    def get_note(note_id, token, breadcrumb):
        """
        Retrieve a specific note document by ID.

        Used internally after create to return the created document.
        """
        try:
            NoteService._check_permission(token, "read")

            mongo = MongoIO.get_instance()
            config = Config.get_instance()
            note = mongo.get_document(config.NOTE_COLLECTION_NAME, note_id)
            if note is None:
                raise HTTPNotFound(f"Note { note_id} not found")

            logger.info(f"Retrieved note { note_id} for user {token.get('user_id')}")
            return note
        except HTTPNotFound:
            raise
        except Exception as e:
            logger.error(f"Error retrieving note { note_id}: {str(e)}")
            raise HTTPInternalServerError(f"Failed to retrieve note { note_id}")
