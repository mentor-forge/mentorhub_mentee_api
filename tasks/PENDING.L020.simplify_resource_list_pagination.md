# L020 – Simplify GET /api/resource list pagination and archived filter

**Status**: Pending  
**Type**: Feature  
**Depends On**: L010  
**Description**: Replace infinite-scroll list pagination on `GET /api/resource` with offset/size **request headers** (defaults `0` / `20`), return a plain JSON array in the response body, and exclude `archived` resources for non-admin callers.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — list contract from L010

Additional inputs:

- `src/routes/resource_routes.py` — reads query params today (`after_id`, `limit`, `sort_by`, `order`, `name`); replace with header-based offset/size
- `src/services/resource_service.py` — `get_resources` uses `execute_infinite_scroll_query`
- `api_utils.Config` — `ROLE_ADMIN` for admin role check (`Config.get_instance().ROLE_ADMIN`)
- `test/routes/test_resource_routes.py`
- `test/services/test_resource_service.py`
- `test/e2e/test_resource.py`

Pattern reference: L010 OpenAPI documents the target contract (array body, `offset`/`size` headers, archived filter). Do not orchestrate this task until the upstream `Resource` schema/configurator change adding `archived` to `resource_status` is actually available.

## Goals

- `GET /api/resource` reads pagination from request headers:
  - `offset` — integer, default `0`
  - `size` — integer, default `20` (enforce the maximum documented in L010)
- Response body is a **JSON array** of `Resource` documents (no `items`/`has_more`/`next_cursor` wrapper).
- Non-admin users: MongoDB query excludes documents where `status` equals `archived`.
- Admin users (`admin` in JWT `roles`, compared via `Config.get_instance().ROLE_ADMIN`): no archived filter — all resources returned, including `archived`.
- Remove infinite-scroll query parameters (`after_id`, `limit`, `sort_by`, `order`) from the route; retain optional `name` query filter if still useful, or remove if not in L010 contract.
- `ResourceService._check_permission` for `read` allows any authenticated user (no additional role gate for list).
- Unit and E2E tests updated for the new response shape and archived filtering behavior.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/routes/test_resource_routes.py` — array response; header defaults; admin vs non-admin filter behavior (mock service).
  - `test/services/test_resource_service.py` — offset/size query; archived exclusion for non-admin; admin sees archived; invalid offset/size raises `HTTPBadRequest` if validated.
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e`
  - `test/e2e/test_resource.py` — assert list response is a JSON array; assert `offset`/`size` headers are honored.
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/routes/resource_routes.py` — header-based offset/size; return `jsonify(array)` not wrapper object
- `src/services/resource_service.py` — replace infinite-scroll with offset/limit MongoDB query; archived status filter for non-admin
- `test/routes/test_resource_routes.py` — updated list route tests
- `test/services/test_resource_service.py` — updated list service tests (pagination + archived filter)
- `test/e2e/test_resource.py` — updated list e2e assertions

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
