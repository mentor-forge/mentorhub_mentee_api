# L181 – Adopt Get List pattern on GET /api/resource

**Status**: Pending  
**Type**: Feature  
**Depends On**: L180  
**Description**: Replace manual offset/size header parsing on `GET /api/resource` with `parse_list_request` from `api_utils.flask_utils.list_request`; pass parsed `filters` and `sort_by` into `ResourceService.get_resources`; document filter query params and order-by in `docs/openapi.yaml`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md` — **Standardized Get List pattern**
- `README.md`
- `docs/openapi.yaml` — current `GET /api/resource` contract from L010/L020

Additional inputs:

- `../mentorhub_api_utils/api_utils/flask_utils/list_request.py` — `parse_list_request`
- `../mentorhub_api_utils/api_utils/services/resource_service.py` — `RESOURCE_LIST_FILTERS`, `RESOURCE_LIST_ORDER`, `get_resources(..., filters, sort_by)`
- `src/routes/resource_routes.py` — reads `offset`/`size` headers manually today; does not pass filters or sort
- `tasks/SHIPPED.L020.simplify_resource_list_pagination.md` — prior list migration pattern
- `tasks/SHIPPED.L170.adopt_api_utils_services.md` — routes import `api_utils.services.ResourceService`

**Filter and order contract** (from api_utils):

| Query param | Type | MongoDB behavior |
|-------------|------|------------------|
| `name` | contains | case-insensitive substring on `name` |
| `description` | contains | case-insensitive substring on `description` |
| `status` | in_list | comma-separated values → `$in` (e.g. `?status=active,draft`) |
| `sort_by` | order | whitelisted: `name`, `description`, `status`, `created.at_time`, `saved.at_time` |
| `order` | order | `asc` or `desc`; default sort `name` asc |

Pagination remains **request headers** `offset` (default `0`) and `size` (default `20`, max `100`). Response body remains a plain JSON array. Non-admin archived exclusion stays in `ResourceService` (no route change).

## Goals

- `GET /api/resource` route uses `parse_list_request(request, RESOURCE_LIST_FILTERS, RESOURCE_LIST_ORDER)` and calls:
  ```python
  ResourceService.get_resources(token, breadcrumb, offset, size, filters, sort_by)
  ```
- Remove local `DEFAULT_OFFSET` / `DEFAULT_SIZE` constants and manual header parsing from `resource_routes.py` (handled by `parse_list_request`).
- Import `RESOURCE_LIST_FILTERS` and `RESOURCE_LIST_ORDER` from `api_utils.services.resource_service`.
- `docs/openapi.yaml` `GET /api/resource` documents:
  - Existing `offset` / `size` header parameters (unchanged).
  - Query parameters: `name`, `description`, `status`, `sort_by`, `order` with descriptions matching api_utils filter/order behavior.
  - `400` response for invalid pagination, filter, or order values (via `validate_pagination` / order validation in `parse_list_request`).
  - Non-admin archived filter behavior (unchanged from L010).
- Route unit tests assert `parse_list_request` wiring: service called with `filters` and `sort_by` kwargs when query params are present.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/routes/test_resource_routes.py` — update mocks for `filters`/`sort_by` kwargs; add cases for filter query params (`?name=`, `?status=`) and `sort_by`/`order`; assert invalid pagination returns `400` if exercised at route layer.
- **Spec validation**
  - `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - `test/e2e/test_resource.py` — existing pagination header test still passes; add E2E for `?name=` filter and `sort_by`/`order` query params when test data supports assertions.
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e`

## Outputs

- `src/routes/resource_routes.py` — adopt `parse_list_request`; pass `filters` and `sort_by` to `ResourceService.get_resources`
- `docs/openapi.yaml` — document filter and order query params on `GET /api/resource`; add `400` response if not already present
- `test/routes/test_resource_routes.py` — updated list route tests with filter/sort kwargs
- `test/e2e/test_resource.py` — filter and sort query param assertions (when test data available)

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
