# L120 – Implement GET /api/journey (token owner's journey, get-or-create)

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L110  
**Description**: Implement `GET /api/journey` to return the authenticated user's Journey (`_id` = token `profile_id`), cloning the template Journey when missing. Remove the infinite-scroll list endpoint and `GET /api/journey/<id>`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — contract from L110
- `tasks/_PLANNING.md` — MongoIO access rules
- `src/routes/journey_routes.py`
- `src/services/journey_service.py`
- `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py` — `get_document`, `create_document`
- `tasks/SHIPPED.L070.refactor_services_to_mongoio.md` — MongoIO patterns

Additional inputs:

- `test/routes/test_journey_routes.py` — remove `@pytest.mark.skip`; replace list/id GET tests
- `test/services/test_journey_service.py` — extend for get-or-create
- `test/e2e/test_journey.py` — remove skip; replace list E2E with get-or-create scenarios
- `test/e2e/e2e_auth.py` — token `profile_id` values

**External prerequisites**:

- Template Journey document `_id` `ffff00000000000000000001` exists in the database after `pipenv run db` (MongoDB T117). If missing, set **Status** to `Blocked` and stop.
- Mentee Journey documents in seed data should use `_id` equal to `profile_id`. Legacy T118 journeys with mismatched ids and invalid `resource_id` values are being fixed in [mentorhub_mongodb_api#45 — F-D19: resource_id test data](https://github.com/mentor-forge/mentorhub_mongodb_api/issues/45). Unit tests mock journeys; E2E against seeded mentee profiles may be deferred until that issue ships.

**Template clone rules** (from L110 / T117):

- Load template by `_id` `ffff00000000000000000001`.
- New document `_id` = token `profile_id`; set `profile_id` to the same value.
- Copy `status`, `library`, `now`, `next`, `later` from template.
- Set fresh `created` and `saved` breadcrumbs; omit template `_id`.

## Goals

- **`JourneyService.get_my_journey(token, breadcrumb)`**:
  - Require `profile_id` on token; raise `HTTPBadRequest` when absent.
  - Look up Journey by `_id` == `profile_id` via `MongoIO.get_document`.
  - When found, return the document.
  - When not found, clone the template (see Context), create via `MongoIO.create_document`, return the created document.
  - Raise `HTTPNotFound` when the template document is missing.
  - `_check_permission(token, 'read')` — any authenticated user with `profile_id`.
- **Remove** `JourneyService.get_journeys` and `ALLOWED_SORT_FIELDS` / infinite-scroll usage.
- **Remove** `JourneyService.get_journey(journey_id, ...)` if no callers remain after route cleanup (or keep as private helper used by get-or-create and PATCH only).
- **`journey_routes.py`**:
  - `GET ""` calls `get_my_journey`; returns `200` + Journey JSON.
  - **Remove** `GET "/<journey_id>"` route handler.
  - **Remove** `GET ""` list/infinite-scroll handler (`get_journeys`).
  - Register more specific PATCH sub-routes in later tasks (L140/L150); ensure route order does not break `GET ""`.
- **Unit tests** (remove module-level skip):
  - `test/services/test_journey_service.py` — get existing journey; get-or-create from template; missing template → 404; missing `profile_id` → 400.
  - `test/routes/test_journey_routes.py` — `GET /api/journey` success and get-or-create; remove list tests.
- **E2E tests** (remove module-level skip):
  - `test/e2e/test_journey.py` — `GET /api/journey` returns journey for token `profile_id`; second GET is idempotent; new profile token triggers clone. Prefer a token whose `profile_id` has no pre-seeded journey (get-or-create path). Full E2E against all mentee seed journeys waits on [mentorhub_mongodb_api#45](https://github.com/mentor-forge/mentorhub_mongodb_api/issues/45).

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_journey_service.py`
  - `test/routes/test_journey_routes.py`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - `test/e2e/test_journey.py` — GET my journey and get-or-create
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e` against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/services/journey_service.py` — `get_my_journey`; remove `get_journeys`; adjust `get_journey` as needed
- `src/routes/journey_routes.py` — `GET /api/journey` only; remove list and GET-by-id handlers
- `test/services/test_journey_service.py` — get-or-create unit tests
- `test/routes/test_journey_routes.py` — updated route tests (no skip)
- `test/e2e/test_journey.py` — updated E2E tests (no skip)

The agent must not update files outside this list.

## Execution Notes

**Summary**
- Implemented `JourneyService.get_my_journey` with template clone from `ffff00000000000000000001`.
- Removed list and GET-by-id routes; `GET /api/journey` returns token owner's journey.
- Rewrote unit, route, and E2E tests (get-or-create with unique profile IDs).

**Testing**
- `pipenv run test`: 96 passed.
- `pipenv run lint` and `pipenv run build`: clean.
