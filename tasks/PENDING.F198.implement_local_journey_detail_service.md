# F198 – Implement local JourneyDetailService (GET profile enrichment)

**Status**: Pending  
**Type**: Feature  
**Depends On**: F197  
**Description**: Add `src/services/journey_detail_service.py` with `get_my_journey_detail` — local implementation to ship and test on this branch before api-utils harvest (see `ISSUE.mentorhub_api_utils.journey_get_profile_enrichment.md`).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — `JourneyDetail` and `Profile` contracts from F197
- `tasks/_PLANNING.md` — MongoIO access rules
- `../mentorhub_api_utils/api_utils/services/journey_service.py` — `get_my_journey` (get-or-create unchanged)
- `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py` — `get_document`
- `../mentorhub_api_utils/api_utils/config/config.py` — `PROFILE_COLLECTION_NAME`
- `tasks/SHIPPED.L194.implement_journey_promote_service.md` — local service before harvest pattern
- `tasks/SHIPPED.L030.resource_detail_aggregation_and_notes.md` — read-time composite pattern
- `tasks/ISSUE.mentorhub_api_utils.journey_get_profile_enrichment.md` — deferred harvest target

Additional inputs:

- `src/services/journey_promote_service.py` — local service conventions in this repo
- `src/services/__init__.py`

**Deferred (not in this task)**: Harvest to `api_utils` and bump `Pipfile` pin — tracked in `ISSUE.mentorhub_api_utils.journey_get_profile_enrichment.md` and follow-on adopt/bump tickets after this workflow ships.

## Goals

- **`JourneyDetailService`** in `src/services/journey_detail_service.py`:
  - **`get_my_journey_detail(token, breadcrumb)`**:
    - Resolve Journey via **`JourneyService.get_my_journey(token, breadcrumb)`** (get-or-create unchanged).
    - Load token owner's Profile via **`MongoIO.get_document(config.PROFILE_COLLECTION_NAME, profile_id)`** where `profile_id` comes from the JWT (same id used for journey ownership).
    - If Profile is missing, fail through normal **`MongoIO` / service not found** exceptions (propagate as `HTTPNotFound` like other domain reads).
    - Return `{**journey, "profile": profile}` — Journey fields at top level plus embedded read-only `profile` (not a nested `{ journey, profile }` wrapper).
  - All MongoDB I/O via **`MongoIO`** only — no direct PyMongo.
  - Do **not** persist `profile` on the Journey collection.
- **`src/services/__init__.py`** — export `JourneyDetailService` if consistent with existing local services.
- **Unit tests** in `test/services/test_journey_detail_service.py`:
  - Success: returns journey fields plus `profile` when Profile exists (mock `JourneyService.get_my_journey`, `MongoIO.get_document`).
  - Missing Profile → not found error.
  - `get_my_journey` failure paths propagate unchanged (missing `profile_id`, template not found).
- No route or OpenAPI changes in this task.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_journey_detail_service.py`
- **Build**
  - `pipenv run build`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/journey_detail_service.py` — new local service (harvest candidate)
- `src/services/__init__.py` — export `JourneyDetailService` if needed
- `test/services/test_journey_detail_service.py` — unit tests

The agent must not update files outside this list.

## Execution Notes
