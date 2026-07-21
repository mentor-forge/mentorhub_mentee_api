# F199 – Wire GET /api/journey profile enrichment and tests

**Status**: Pending  
**Type**: Feature  
**Depends On**: F198  
**Description**: Switch `GET /api/journey` to local `JourneyDetailService.get_my_journey_detail`. Confirm PATCH and mutation endpoints return plain Journey documents without `profile` and reject `profile` in PATCH bodies.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — `JourneyDetail`, `Profile`, and mutation contracts from F197
- `tasks/_PLANNING.md` — MongoIO access rules
- `src/services/journey_detail_service.py` — from F198
- `src/routes/journey_routes.py` — `GET ""` currently calls `JourneyService.get_my_journey`
- `../mentorhub_api_utils/api_utils/services/journey_service.py` — PATCH/mutations unchanged
- `test/routes/test_journey_routes.py`
- `test/e2e/test_journey.py`
- `test/e2e/e2e_auth.py` — token `profile_id` values aligned with seeded Profile documents
- `tasks/SHIPPED.L195.implement_journey_promote_path.md` — route wiring pattern

**Deferred (not in this task)**: Harvest `JourneyDetailService` to `api_utils`, bump pin, and switch imports — see `ISSUE.mentorhub_api_utils.journey_get_profile_enrichment.md`.

**External prerequisites**:

- F197 OpenAPI and F198 local service shipped.
- Seeded test data includes Profile documents whose `_id` matches mentee token `profile_id` values used in E2E (e.g. `e00000000000000000000001`). If profiles are missing for E2E personas, set **Status** to `Blocked` and stop.

## Goals

- **`src/routes/journey_routes.py`**:
  - `GET /api/journey` calls **`JourneyDetailService.get_my_journey_detail(token, breadcrumb)`** instead of `JourneyService.get_my_journey`.
  - PATCH and mutation route handlers unchanged — they continue calling `JourneyService` / `JourneyPromoteService` methods that return plain Journey documents **without** `profile`.
  - **`PATCH /api/journey/{journey_id}`**: reject request body containing `profile` with **`403`** before calling `JourneyService.update_journey` (local guard until harvest adds `profile` to api-utils `RESTRICTED_UPDATE_FIELDS`).
- **GET response shape** matches OpenAPI **`JourneyDetail`**: Journey fields at top level plus embedded **`profile`** object.
- **Missing Profile** on GET fails with normal not-found handling.
- **Mutation responses** (`advance`, `complete`, `promote/path`, `promote/module`) return plain **`Journey`** without `profile` key (unchanged service behavior).
- **Unit tests** (`test/routes/test_journey_routes.py`):
  - `GET /api/journey` mocks `JourneyDetailService.get_my_journey_detail`; asserts `200` and response includes `profile`.
  - PATCH success response does **not** include `profile`.
  - PATCH with `{ "profile": { ... } }` returns `403`.
  - At least one mutation route test asserts response JSON has no `profile` key.
- **E2E tests** (`test/e2e/test_journey.py`):
  - Extend `test_get_my_journey_endpoint` (or add sibling test): `GET /api/journey` response includes `profile` with `_id` equal to token `profile_id`.
  - Optional: PATCH mutation response lacks `profile` (SPA refetches GET separately).

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/routes/test_journey_routes.py` — GET detail with profile; PATCH/mutation omit profile; PATCH rejects profile body
  - `test/services/test_journey_detail_service.py` — still passes from F198
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e`
  - `test/e2e/test_journey.py` — GET includes embedded profile
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API
  - Confirm served OpenAPI matches F197: `curl -s http://localhost:8393/docs/openapi.yaml | grep -A2 JourneyDetail`

## Outputs

Paths are relative to the **API repository root**.

- `src/routes/journey_routes.py` — `GET /api/journey` uses `JourneyDetailService`; PATCH rejects `profile` in body
- `test/routes/test_journey_routes.py` — GET profile enrichment; PATCH/mutation omit profile; PATCH rejects profile
- `test/e2e/test_journey.py` — GET response includes embedded profile

The agent must not update files outside this list.

## Execution Notes
