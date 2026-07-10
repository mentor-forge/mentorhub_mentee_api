# L090 – Simplify GET /api/path to return all paths sorted by name

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L080  
**Description**: Replace infinite-scroll list pagination on `GET /api/path` with a plain JSON array of all Path documents sorted by `name` ascending. Remove pagination, cursor, and sort query parameters from the route and service.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — list contract from L080

Additional inputs:

- `src/routes/path_routes.py` — reads `after_id`, `limit`, `sort_by`, `order`, `name` query params today; return wrapper object
- `src/services/path_service.py` — `get_paths` uses `execute_infinite_scroll_query` via `mongo.get_collection`
- `src/services/resource_service.py` — reference for `mongo.get_documents` + sort pattern (`get_resources`)
- `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py` — `MongoIO.get_documents`
- `test/routes/test_path_routes.py`
- `test/services/test_path_service.py`
- `test/e2e/test_path.py`

Pattern reference: L080 OpenAPI documents the target contract (array body, fixed name sort, no pagination). `tasks/SHIPPED.L020.simplify_resource_list_pagination.md` shows the list-endpoint migration pattern. See `tasks/_PLANNING.md` for allowed external repos and MongoDB schema discovery.

## Goals

- `GET /api/path` response body is a **JSON array** of `Path` documents (no `items` / `has_more` / `next_cursor` / `limit` wrapper).
- `PathService.get_paths(token, breadcrumb)` returns a `list` of Path documents sorted by `name` ascending.
- MongoDB query uses `MongoIO.get_documents(config.PATH_COLLECTION_NAME, sort_by=[("name", ASCENDING)])` (empty or minimal `match` as appropriate).
- Remove infinite-scroll and pagination query parameters from the route (`after_id`, `limit`, `sort_by`, `order`); remove optional `name` filter unless L080 documents it (default: no query params).
- Remove `ALLOWED_SORT_FIELDS` and `execute_infinite_scroll_query` usage from `path_service.py`.
- Route all MongoDB reads through `MongoIO.get_documents` with `sort_by=[("name", ASCENDING)]` — do **not** call `mongo.get_collection(...).find(...)` or `execute_infinite_scroll_query` (see `tasks/_PLANNING.md` and `SHIPPED.L070.refactor_services_to_mongoio.md`).
- `PathService._check_permission` for `read` allows any authenticated user (unchanged placeholder behavior).
- Unit and E2E tests updated for the new response shape and simplified service signature.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/routes/test_path_routes.py` — array response; service called without pagination/cursor args.
  - `test/services/test_path_service.py` — returns list sorted by name via `get_documents`; remove infinite-scroll validation tests (`limit`, `after_id`, `sort_by`, `order`).
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e`
  - `test/e2e/test_path.py` — assert list response is a JSON array (not a dict wrapper).
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/routes/path_routes.py` — remove pagination/scroll query params; return `jsonify(array)` not wrapper object
- `src/services/path_service.py` — replace infinite-scroll with `MongoIO.get_documents` sorted by name
- `test/routes/test_path_routes.py` — updated list route tests
- `test/services/test_path_service.py` — updated list service tests
- `test/e2e/test_path.py` — updated list e2e assertions

The agent must not update files outside this list.

## Execution Notes

**Summary of changes**
- `GET /api/path` returns a plain JSON array sorted by name via `MongoIO.get_documents`.
- Removed infinite-scroll query parameters and wrapper response from route and service.

**Testing results**
- `pipenv run test`: path list unit tests pass.
- `pipenv run e2e` (`test/e2e/test_path.py::test_get_paths_endpoint`): passed against containerized API.
