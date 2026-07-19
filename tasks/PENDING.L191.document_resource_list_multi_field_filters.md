# L191 – Document Resource list multi-field search filters

**Status**: Pending  
**Type**: Feature  
**Depends On**: L190  
**Description**: Document optional `url`, `interests`, `technologies`, and `skill_level` query filters on `GET /api/resource` in `docs/openapi.yaml` (and the route docstring), matching `RESOURCE_LIST_FILTERS` from `api-utils==0.5.1`. Clarify that multiple filters are ANDed. Leave pagination headers, sort, and existing `name` / `description` / `status` behavior unchanged.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md` — **Standardized Get List pattern**
- `README.md`
- `docs/openapi.yaml` — current `GET /api/resource` filter docs from L181

Additional inputs:

- `../mentorhub_api_utils/api_utils/services/resource_service.py` — `RESOURCE_LIST_FILTERS` in `0.5.1`
- `src/routes/resource_routes.py` — list route docstring still lists only `name`, `description`, `status`
- `tasks/SHIPPED.L181.adopt_resource_list_get_list.md` — prior OpenAPI filter documentation pattern
- `tasks/ISSUE.mentorhub_api_utils.extend_resource_list_filters.md` — resolved handoff / confirmed contract

**Filter contract to document** (runtime provided by `api-utils==0.5.1` after L190):

| Query param | Behavior |
|-------------|----------|
| `url` | Case-insensitive substring (`contains`) on `url` |
| `interests` | Comma-separated `$in` on `interests` array (any-element match) |
| `technologies` | Comma-separated `$in` on `technologies` array |
| `skill_level` | Comma-separated `$in` on `skill_level` |

Multiple query filters are **AND**ed (same as today’s `name` + `description` + `status` composition). No single free-text `q` / OR-across-fields parameter.

Field names: **`technologies`** (plural), **`skill_level`**.

## Goals

- `docs/openapi.yaml` `GET /api/resource` operation description lists the four new filters alongside existing ones and states that provided filters are ANDed.
- OpenAPI parameters section adds optional query params `url`, `interests`, `technologies`, and `skill_level` with descriptions and examples (mirror style of `name` / `description` / `status`).
- Existing params and behavior unchanged: `name`, `description`, `status`, `sort_by`, `order`, `offset`/`size` headers, non-admin archived exclusion, response shape.
- `src/routes/resource_routes.py` list handler docstring mentions the new query params.
- Spec parses; served OpenAPI at `/docs/openapi.yaml` includes the new parameters.
- No filter-implementation changes in this API — filters come from imported `RESOURCE_LIST_FILTERS`.

## Testing Expectations

Run all commands from the **API repository root**.

- **Spec validation**
  - `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - Confirm new param names appear in the loaded `GET /api/resource` parameters list
- **Lint**
  - `pipenv run lint`
- **Unit tests**
  - `pipenv run test` — no intentional test expansions here (L192); suite remains green
- **Build**
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`
  - Verify served spec: `curl -s http://localhost:8393/docs/openapi.yaml` includes `url`, `interests`, `technologies`, and `skill_level` under the resource list operation

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — document `url`, `interests`, `technologies`, `skill_level` on `GET /api/resource`; document AND composition
- `src/routes/resource_routes.py` — update list-route docstring query-param list only

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
