# T201 – Simplify GET /api/event list pagination

**Status**: Pending  
**Type**: Feature  
**Depends On**: T200  
**Description**: Implement `GET /api/event` with offset/size **request headers** (defaults `0` / `20`), return a plain JSON array in the response body, and replace the legacy infinite-scroll list pattern removed in L060.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — list contract from T200
- `tasks/SHIPPED.L020.simplify_resource_list_pagination.md` — offset/size header pattern (routes + service + tests)
- `tasks/SHIPPED.L070.refactor_services_to_mongoio.md` — MongoIO-only data access; use `get_documents` + slice until server-side skip/limit exists in api_utils

Additional inputs:

- `src/routes/event_routes.py` — POST-only today; add GET list handler
- `src/services/event_service.py` — add `get_events`; keep `create_event` and `get_event`
- `src/routes/resource_routes.py` — header parsing reference (`DEFAULT_OFFSET`, `DEFAULT_SIZE`)
- `src/services/resource_service.py` — `_validate_pagination` and `get_documents` + slice pattern
- `test/routes/test_event_routes.py`
- `test/services/test_event_service.py`
- `test/e2e/test_event.py`
- `test/test_server.py` — route registration assertions

MongoDB access: route all I/O through `MongoIO.get_documents` — do not call PyMongo `collection.find` directly.

## Goals

- **`GET /api/event`** route in `src/routes/event_routes.py`:
  - Reads pagination from request headers: `offset` (default `0`), `size` (default `20`, max `100`).
  - Returns `jsonify(events)` where `events` is a JSON **array** (not a wrapper object).
  - Requires valid JWT (`create_flask_token` / `create_flask_breadcrumb`).
- **`EventService.get_events(token, breadcrumb, offset=0, size=20)`**:
  - `_check_permission(token, 'read')` — any authenticated user.
  - Validate `offset` / `size` (reuse resource-style rules: `offset >= 0`, `1 <= size <= 100`; raise `HTTPBadRequest` on violation).
  - Fetch events via `MongoIO.get_documents` on `Config.EVENT_COLLECTION_NAME`.
  - Sort newest-first by `created.at_time` descending before slicing `[offset:offset+size]` (match T200 contract intent).
  - Return a plain `list` of event documents.
- **Do not** reintroduce `GET /api/event/<event_id>` in this task unless already required by T200 (list-only scope).
- **Unit tests**:
  - `test/routes/test_event_routes.py` — GET returns array; header defaults and custom `offset`/`size` passed to service.
  - `test/services/test_event_service.py` — pagination slice; invalid offset/size raises `HTTPBadRequest`; sort order (newest first).
- **E2E tests**:
  - `test/e2e/test_event.py` — `GET /api/event` returns JSON array; `offset`/`size` headers honored; auth required.
- **`test/test_server.py`** — confirm GET `/api/event` is registered (in addition to POST).
- `pipenv run test`, `pipenv run lint`, and `pipenv run build` pass.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/routes/test_event_routes.py` — GET list route
  - `test/services/test_event_service.py` — `get_events` pagination and validation
  - `test/test_server.py` — route registration
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e`
  - `test/e2e/test_event.py` — GET list array shape and header pagination
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/routes/event_routes.py` — add GET list handler with header-based offset/size
- `src/services/event_service.py` — add `get_events` with pagination validation and MongoIO list fetch
- `test/routes/test_event_routes.py` — GET list route tests
- `test/services/test_event_service.py` — `get_events` unit tests
- `test/e2e/test_event.py` — GET list E2E tests
- `test/test_server.py` — updated route registration assertions

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
