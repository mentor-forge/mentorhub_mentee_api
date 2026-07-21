# Harvest Journey GET profile enrichment into api-utils

**Status**: Open (deferred until local implementation ships)

## Summary

`mentorhub_mentee_api` implements GET profile enrichment **locally** in `src/services/journey_detail_service.py` so the feature can ship and be tested on this branch without waiting on a new `api-utils` release. The logic should be **harvested** into `api_utils.services.journey_service` following the same pattern as `ISSUE.mentorhub_api_utils.harvest_journey_promote_mutations.md`.

Design mirrors the **`ResourceDetail`** read-time composite pattern: the MongoDB Journey document is unchanged; `profile` is **not** persisted on the Journey collection.

## Source (this repo)

Harvest from:

- `src/services/journey_detail_service.py` — `JourneyDetailService.get_my_journey_detail`
- `test/services/test_journey_detail_service.py` — port tests to `mentorhub_api_utils/tests/services/test_journey_service.py`
- `src/routes/journey_routes.py` — PATCH `profile` rejection guard (move into api-utils `RESTRICTED_UPDATE_FIELDS` on harvest)

## Required upstream changes (`mentorhub_api_utils`)

1. **`JourneyService.get_my_journey_detail(token, breadcrumb)`** on the shared class:
   - Call existing `get_my_journey(token, breadcrumb)`.
   - Load Profile via `MongoIO.get_document(config.PROFILE_COLLECTION_NAME, profile_id)`.
   - Missing Profile → normal not found exceptions.
   - Return `{**journey, "profile": profile}`.

2. **Keep mutation paths unchanged** — `get_my_journey`, `update_journey`, `advance_resource`, `complete_resource`, and promote helpers return plain Journey documents without `profile`.

3. **`RESTRICTED_UPDATE_FIELDS`** — add `"profile"` so route-level PATCH guard can be removed after adopt.

4. Unit tests in `mentorhub_api_utils/tests/services/test_journey_service.py`.

5. Publish new **`api-utils`** patch/minor to CodeArtifact.

## Follow-on (this repo)

After upstream ships, run deferred adopt/bump tickets (same pattern as `ISSUE.mentorhub_api_utils.adopt_journey_promote_from_api_utils.md`):

- Bump `api-utils` pin in `Pipfile`
- Switch `GET /api/journey` to `JourneyService.get_my_journey_detail`
- Remove local `journey_detail_service.py` and duplicate tests
- Remove route-level PATCH `profile` guard (handled by api-utils)

## Notes

- Do **not** add a Profile read endpoint to the Mentee API for this feature.
- Do **not** accept `profile` on `JourneyUpdate` or persist it on Journey documents.
- **Local workflow tasks** (run first on this branch): F197 → F198 → F199.
