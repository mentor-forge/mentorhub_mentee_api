# L060 – Align Note and Event runtime with POST-only contract

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L040  
**Description**: Remove Event GET routes, prune unused Note read/update service surface, delete orphaned Rating test artifacts, and update tests so runtime behavior matches the L040 OpenAPI contract (Note and Event POST-only).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — L040 POST-only Note/Event contract
- `src/routes/note_routes.py` — already POST-only; confirm no GET/PATCH handlers
- `src/routes/event_routes.py` — still exposes GET list and GET by id (remove)
- `src/services/note_service.py` — retain methods still needed internally (`create_note`, `get_note` for POST response echo, `get_notes_for_resource` for aggregation)
- `src/services/event_service.py` — retain `create_event` and internal `get_event` used by POST response echo; remove or stop exporting unused list/get helpers if no callers remain
- `tasks/PENDING.L040.cleanup_openapi_aggregation_note_event.md` — target API contract

Additional inputs:

- `test/routes/test_event_routes.py`
- `test/routes/test_note_routes.py`
- `test/services/test_note_service.py`
- `test/services/test_event_service.py`
- `test/e2e/test_note.py`
- `test/e2e/test_event.py`
- `test/e2e/test_rating.py` — orphaned Rating E2E (remove if present)
- `test/test_server.py` — route registration assertions

## Goals

- **Event routes — POST only**:
  - Remove `GET /api/event` (list/infinite scroll) and `GET /api/event/<event_id>` handlers from `src/routes/event_routes.py`.
  - Update module docstring to describe POST-only semantics.
  - Keep `POST /api/event` unchanged (create event, return created document).
- **Note routes — confirm POST only**:
  - Verify `src/routes/note_routes.py` exposes only `POST /api/note` (no code changes expected unless stray GET/PATCH handlers exist).
- **Service layer cleanup** (remove dead public API aligned to removed HTTP operations):
  - `NoteService`: remove `get_notes` (infinite-scroll list) and `update_note` if no remaining callers; keep `create_note`, `get_note` (POST response), and `get_notes_for_resource` (aggregation).
  - `EventService`: remove `get_events` (list) if no remaining callers after route removal; keep `create_event` and `get_event` (POST response).
- **Remove orphaned Rating artifacts**:
  - Delete `test/e2e/test_rating.py` if present.
  - Remove any stale compiled artifacts referencing removed Rating code (e.g. orphaned `.pyc` under `src/services/` for deleted `rating_service.py`) — do not recreate Rating service code.
- **Tests updated**:
  - `test/routes/test_event_routes.py` — remove GET route tests; keep POST tests; remove module-level skip if tests are now aligned with current Event schema.
  - `test/services/test_event_service.py` — remove or adjust tests for deleted list/get service methods.
  - `test/services/test_note_service.py` — remove tests for deleted `get_notes`/`update_note` methods; keep create and `get_notes_for_resource` coverage.
  - `test/e2e/test_event.py` — POST-only E2E; remove GET list/by-id tests.
  - `test/e2e/test_note.py` — POST-only E2E; remove GET list/filter tests; align create payload with Note dictionary fields (`resource_id`, `note`, etc.).
  - `test/test_server.py` — Event route registration check should use POST (not GET); confirm no Rating routes registered.
- `pipenv run test`, `pipenv run lint`, and `pipenv run build` pass.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/routes/test_event_routes.py` — POST-only
  - `test/routes/test_note_routes.py` — POST-only
  - `test/services/test_event_service.py` — aligned service surface
  - `test/services/test_note_service.py` — aligned service surface
  - `test/test_server.py` — route registration
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - `test/e2e/test_note.py` — POST create only
  - `test/e2e/test_event.py` — POST create only
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e` against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/routes/event_routes.py` — remove GET handlers; POST-only
- `src/services/note_service.py` — remove unused list/update methods
- `src/services/event_service.py` — remove unused list method(s)
- `test/routes/test_event_routes.py` — POST-only tests
- `test/services/test_note_service.py` — remove obsolete test cases
- `test/services/test_event_service.py` — remove obsolete test cases
- `test/e2e/test_note.py` — POST-only E2E
- `test/e2e/test_event.py` — POST-only E2E
- `test/e2e/test_rating.py` — **delete**
- `test/test_server.py` — updated route registration assertions

The agent must not update files outside this list.

## Execution Notes

**Summary**
- Removed Event GET routes; Event and Note services trimmed to POST/create surface plus internal helpers.
- Rewrote Note/Event unit and E2E tests for POST-only contract and current MongoDB schemas.
- Updated `test_server.py` for POST event registration and aggregation blueprint.
- Removed stale `rating_service.pyc` artifact.

**Testing**
- `pipenv run test`: 78 passed, 24 skipped, 19 deselected.
- `pipenv run build`: clean.
