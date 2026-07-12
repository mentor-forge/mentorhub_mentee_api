# L184 – Update list endpoint tests for Get List adoption

**Status**: Pending  
**Type**: Feature  
**Depends On**: L181, L182, L183  
**Description**: Final test sweep after api-utils 0.5.0 list adoption: ensure route mocks match new service kwargs across list endpoints; E2E tests assert header pagination and filter query params on resource and path lists; fix any remaining failures from breaking path pagination.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md` — **Standardized Get List pattern**
- `README.md`

Additional inputs:

- `tasks/PENDING.L181.adopt_resource_list_get_list.md` — resource list route/OpenAPI/test changes
- `tasks/PENDING.L182.adopt_path_list_pagination.md` — path list breaking pagination
- `tasks/PENDING.L183.verify_composite_full_notes.md` — composite note regression tests
- `test/routes/test_resource_routes.py`
- `test/routes/test_path_routes.py`
- `test/e2e/test_resource.py`
- `test/e2e/test_path.py`
- `test/e2e/test_aggregation.py` — uses `GET /api/resource` list to obtain resource ids; may need pagination headers after L182

Sweep any other tests that call list endpoints or mock `ResourceService.get_resources` / `PathService.get_paths` with the pre-0.5.0 signatures (search `test/` for these symbols).

## Goals

- All route unit tests mock `ResourceService.get_resources` and `PathService.get_paths` with the 0.5.0 signature: `(token, breadcrumb, offset, size, filters, sort_by)`.
- Route tests cover:
  - Default pagination (`offset=0`, `size=20`) when headers omitted.
  - Custom `offset`/`size` headers forwarded to service.
  - Filter query params parsed and passed as `filters` dict.
  - Invalid pagination (e.g. negative offset, size > 100) returns `400` at route layer.
- E2E list tests cover:
  - `GET /api/resource` with `offset`/`size` headers and `?name=` / `?status=` filters.
  - `GET /api/path` with `offset`/`size` headers; result length respects `size`.
  - `GET /api/path` with `?name=` filter when matching seed data exists.
  - Aggregation E2E list bootstrap uses sufficient `size` header when fetching resources for detail tests.
- Full suite green: `pipenv run test`, `pipenv run e2e` (containerized).

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test` — full unit suite
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e` — final gate for the Get List adoption workflow

## Outputs

- `test/routes/test_resource_routes.py` — consolidated list mock/signature tests (dedupe with L181 if already complete)
- `test/routes/test_path_routes.py` — consolidated list mock/signature tests (dedupe with L182 if already complete)
- `test/e2e/test_resource.py` — pagination and filter E2E coverage
- `test/e2e/test_path.py` — pagination and filter E2E coverage
- `test/e2e/test_aggregation.py` — update resource list bootstrap call if needed for paginated resource list

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
