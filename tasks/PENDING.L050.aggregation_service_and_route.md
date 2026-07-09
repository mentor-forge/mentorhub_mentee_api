# L050 – Aggregation service, route, and mutation helpers

**Status**: Pending  
**Type**: Feature  
**Depends On**: L040  
**Description**: Extend `AggregationService` with get-or-create detail reads (including related notes via `NoteService`), increment helpers for future Event/Journey callers, and expose `GET /api/aggregation/{resource_id}`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — `AggregationDetail` contract from L040
- `src/services/aggregation_service.py` — existing read-by-`resource_id` helper
- `src/services/note_service.py` — `get_notes_for_resource` for service-to-service note lookup
- `api_utils.Config` — `RESOURCE_AGGREGATION_COLLECTION_NAME`, `ROLE_MENTEE` (default `"mentee"`)
- `../mentorhub_mongodb_api/configurator/dictionaries/Resource_Aggregation.1.0.0.yaml`
- `../mentorhub_mongodb_api/erd.svg` — Resource ↔ Note ↔ Resource_Aggregation relationships
- `tasks/SHIPPED.L030.resource_detail_aggregation_and_notes.md` — service-to-service pattern reference

Additional inputs:

- `src/server.py` — route registration
- `test/services/test_aggregation_service.py` — extend existing tests
- `test/routes/test_resource_routes.py` — route test patterns

## Goals

- **`AggregationService` enhancements** (`src/services/aggregation_service.py`):
  - **`get_aggregation_detail(resource_id, token, breadcrumb)`**:
    - `_check_permission(token, 'read')` — any authenticated user (no additional role gate).
    - Validate `resource_id` as a MongoDB ObjectId (`400` on invalid).
    - Look up aggregation by `resource_id`; if none exists, **create** a new document with:
      - `resource_id`, zeroed counters (`note_count`, `completions`, `hits`, `rating_count`), `rating_sum: 0`, zero/initial `duration`, and `created`/`last_saved` breadcrumbs.
    - Fetch related notes via **service-to-service** call to `NoteService.get_notes_for_resource` (import inside method to avoid circular imports).
    - Return `{ "aggregation": <ResourceAggregation>, "notes": [<Note>, ...] }`.
  - **`add_completion(resource_id, rating, note, duration, token, breadcrumb)`**:
    - `_check_permission(token, 'add_completion')` — **mentee role only** (`Config.ROLE_MENTEE` in token `roles`; raise `403` otherwise).
    - Ensure aggregation exists (get-or-create using the same initializer as above).
    - Increment `completions`, `rating_count`, and `rating_sum` by `rating`.
    - Add `duration` to the aggregated `duration` field (ISO 8601 duration arithmetic).
    - When `note` is provided, create a related Note via `NoteService.create_note` (include `resource_id` and note text) and increment `note_count`.
    - Update `last_saved` breadcrumb.
    - Return the updated aggregation document.
    - **No HTTP route in this task** — reserved for future Journey-complete integration.
  - **`add_hit(resource_id, token, breadcrumb)`**:
    - `_check_permission(token, 'add_hit')` — any authenticated user.
    - Ensure aggregation exists (get-or-create).
    - Increment `hits` by 1 and update `last_saved`.
    - Return the updated aggregation document.
    - **No HTTP route in this task** — reserved for future POST Event follow-link integration.
  - Keep existing `get_aggregation_for_resource` for callers that need aggregation only (e.g. `ResourceService`); it may delegate to shared get-or-create logic internally.
- **New route** `src/routes/aggregation_routes.py`:
  - `GET /api/aggregation/<resource_id>` — calls `AggregationService.get_aggregation_detail`; returns `AggregationDetail` JSON (`200`).
- **Register blueprint** in `src/server.py` at `/api/aggregation`; update route logging summary.
- **Unit tests**:
  - `test/services/test_aggregation_service.py` — get-or-create detail, notes included via mocked `NoteService`, `add_completion` mentee RBAC (403 for non-mentee), `add_hit` open to any authenticated caller, counter increments.
  - `test/routes/test_aggregation_routes.py` — **new** — GET returns composite shape; auth required.
- **E2E** (optional if test data supports it):
  - `test/e2e/test_aggregation.py` — **new** — `GET /api/aggregation/{resource_id}` returns `{ aggregation, notes }`; creates aggregation when missing.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_aggregation_service.py` — detail, get-or-create, `add_completion`, `add_hit`, RBAC
  - `test/routes/test_aggregation_routes.py` — GET route
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - `test/e2e/test_aggregation.py` — aggregation GET composite and get-or-create behavior
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e` against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/services/aggregation_service.py` — `get_aggregation_detail`, `add_completion`, `add_hit`; shared get-or-create helper
- `src/routes/aggregation_routes.py` — **new** GET route blueprint
- `src/server.py` — register aggregation blueprint
- `test/services/test_aggregation_service.py` — extended unit tests
- `test/routes/test_aggregation_routes.py` — **new** route unit tests
- `test/e2e/test_aggregation.py` — **new** E2E tests

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
