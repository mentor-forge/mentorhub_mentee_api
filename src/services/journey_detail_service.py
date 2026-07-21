"""
Local Journey GET profile enrichment.

Temporary implementation in this API repo until harvested into api_utils.services.journey_service.
See tasks/ISSUE.mentorhub_api_utils.journey_get_profile_enrichment.md.
"""

import logging

from api_utils import MongoIO, Config
from api_utils.services import JourneyService
from api_utils.flask_utils.exceptions import (
    HTTPBadRequest,
    HTTPInternalServerError,
    HTTPNotFound,
)

logger = logging.getLogger(__name__)


class JourneyDetailService:
    """Embed token owner's Profile on GET /api/journey responses."""

    @staticmethod
    def get_my_journey_detail(token, breadcrumb):
        try:
            profile_id = token.get("profile_id")
            if not profile_id:
                raise HTTPBadRequest("profile_id is required on token")

            journey = JourneyService.get_my_journey(token, breadcrumb)

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
