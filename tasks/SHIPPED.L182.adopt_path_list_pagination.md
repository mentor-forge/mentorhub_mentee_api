# L182 – Adopt paginated Get List on GET /api/path (breaking)

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L180  
**Description**: **Breaking change**: `PathService.get_paths` in api-utils 0.5.0 paginates by default (`offset=0`, `size=20`). Update `GET /api/path` to read `offset`/`size` headers and optional filter/sort query params via `parse_list_request`; align OpenAPI and tests — callers no longer receive the full path collection without paging.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md` — **Standardized Get List pattern**
- `README.md`
- `docs/openapi.yaml` — current `GET /api/path` contract from L080/L090 (documents full collection, no pagination)

Additional inputs:

- `../mentorhub_api_utils/api_utils/flask_utils/list_request.py` — `parse_list_request`
- `../mentorhub_api_utils/api_utils/services/path_service.py` — `PATH_LIST_FILTERS`, `PATH_LIST_ORDER`, paginated `get_paths`
- `src/routes/path_routes.py` — calls `PathService.get_paths(token, breadcrumb)` with no pagination today
- `tasks/SHIPPED.L090.simplify_path_list.md` — prior contract (full sorted array)
- `tasks/SHIPPED.L080.update_path_openapi.md` — OpenAPI to supersede

**Filter and order contract** (from api_utils):

| Query param | Type | MongoDB behavior |
|-------------|------|------------------|
| `name` | contains | case-insensitive substring on `name` |
| `sort_by` | order | whitelisted: `name` |
| `order` | order | `asc` or `desc`; default sort `name` asc |

Pagination: request headers `offset` (default `0`), `size` (default `20`, max `100`). Response body: plain JSON array (page slice, not full collection).

## Goals

- `GET /api/path` route uses `parse_list_request(request, PATH_LIST_FILTERS, PATH_LIST_ORDER)` and calls:
  ```python
  PathService.get_paths(token, breadcrumb, offset, size, filters, sort_by)
  ```
- Import `PATH_LIST_FILTERS` and `PATH_LIST_ORDER` from `api_utils.services.path_service`.
- `docs/openapi.yaml` `GET /api/path` updated to **replace** the L080/L090 full-collection contract:
  - Document `offset` / `size` header parameters (defaults `0` / `20`, max size `100`).
  - Document optional `name` filter and `sort_by` / `order` query params.
  - Remove language stating "all paths" / "no pagination".
  - Add `400` response for invalid pagination or order values.
  - Retain plain JSON array response schema.
- Route unit tests pass `offset`/`size`/`filters`/`sort_by` to mocked service; default call uses `offset=0`, `size=20`.
- E2E tests assert pagination headers limit result length; document that un-paged clients must iterate with headers.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/routes/test_path_routes.py` — update `get_paths` mock assertions for pagination kwargs; add header and filter query param cases.
- **Spec validation**
  - `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - `test/e2e/test_path.py` — add pagination header test (`size=5` limits array length); update list test docstrings to reflect paged contract; ensure path detail test still obtains a path id (may need larger `size` header or dedicated lookup if seed data exceeds default page).
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e`

## Outputs

- `src/routes/path_routes.py` — adopt `parse_list_request`; pass pagination, filters, and sort to `PathService.get_paths`
- `docs/openapi.yaml` — paginated `GET /api/path` contract with headers, filters, and order params
- `test/routes/test_path_routes.py` — updated list route tests for new service signature
- `test/e2e/test_path.py` — pagination header assertions; adjust detail test if default page no longer includes seed path

The agent must not update files outside this list.

## Execution Notes

**Summary of changes**
- `GET /api/path` uses `parse_list_request` with `PATH_LIST_FILTERS`/`PATH_LIST_ORDER`.
- OpenAPI updated for paginated path list (breaking: no longer returns full collection by default).
- Route and E2E tests cover pagination headers and name filter.

**Test results**
- `pipenv run test`: 46 passed
- `pipenv run lint`: pass
- `pipenv run build`: pass
- `pipenv run container` + `pipenv run api` + path E2E: passed
