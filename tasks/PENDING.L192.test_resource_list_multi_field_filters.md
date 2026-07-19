# L192 – Test Resource list multi-field search filters

**Status**: Pending  
**Type**: Feature  
**Depends On**: L191  
**Description**: Add route unit tests and E2E coverage for the new `GET /api/resource` query filters (`url`, `interests`, `technologies`, `skill_level`) provided by `api-utils==0.5.1`: empty/omitted, match, no-match, and combined filters with offset/size pagination headers.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md` — **Standardized Get List pattern**
- `README.md`
- `docs/openapi.yaml` — L191 documented filter contract

Additional inputs:

- `src/routes/resource_routes.py` — uses `parse_list_request(..., RESOURCE_LIST_FILTERS, ...)`
- `test/routes/test_resource_routes.py` — existing filter/sort mock coverage from L181/L184
- `test/e2e/test_resource.py` — existing `?name=` / `?status=` E2E coverage
- `tasks/SHIPPED.L184.update_list_endpoint_tests.md` — prior list test sweep pattern
- `../mentorhub_api_utils/tasks/SHIPPED.R057.test_resource_list_multi_field_filters.md` — upstream unit coverage of filter parsing/match
- `tasks/ISSUE.mentorhub_api_utils.extend_resource_list_filters.md` — resolved filter semantics

**Expected filter parsing** (via `parse_list_request` + `RESOURCE_LIST_FILTERS` from `0.5.1`):

| Query | Parsed `filters` shape (when present) |
|-------|----------------------------------------|
| `?url=example` | `{"url": "example"}` (`contains`) |
| `?interests=a,b` | `{"interests": ["a", "b"]}` (`in_list`) |
| `?technologies=x` | `{"technologies": ["x"]}` |
| `?skill_level=beginner` | `{"skill_level": ["beginner"]}` |
| omitted / empty | key absent from `filters` |

Combined filters AND together at the Mongo layer (asserted indirectly via E2E result sets when seed data allows). Upstream already covers `list_query` / `RESOURCE_LIST_FILTERS` unit behavior in R057; this task covers mentee route wiring and HTTP E2E.

## Goals

- Route unit tests assert `ResourceService.get_resources` is called with `filters` containing each new param when present on the query string, and that empty/omitted params do not add keys.
- At least one route test covers combining a new filter with existing filters and/or pagination headers (`offset`/`size`).
- E2E tests cover each new filter where seed data supports assertions: match returns expected subset; no-match returns empty (or excludes known non-matching docs); empty/omitted does not error and preserves prior list behavior.
- E2E includes at least one case combining a new filter with `offset`/`size` headers (and optionally with `name` or `description`).
- Full suite green: unit, lint, build, containerized E2E.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e`
  - Optionally spot-check: `curl` with `Authorization` and query params for `url` / `interests` / `technologies` / `skill_level` against the containerized API

If seed data lacks values for a given field, document the gap in **Execution Notes** and cover that filter at the route-mock layer; prefer adding minimal E2E assertions when data exists rather than inventing fixtures outside this API’s test harness.

## Outputs

Paths are relative to the **API repository root**.

- `test/routes/test_resource_routes.py` — unit coverage for new filter query params (empty, present, combined with pagination/other filters)
- `test/e2e/test_resource.py` — E2E coverage for new filters and pagination combination where seed data allows

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
