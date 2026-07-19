# L190 – Bump api-utils to 0.5.1 for Resource list multi-field filters

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Pin and install `api-utils==0.5.1` so `RESOURCE_LIST_FILTERS` includes `url`, `interests`, `technologies`, and `skill_level`, and `parse_list_request` on `GET /api/resource` accepts those query params without route-layer filter wiring changes.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md` — **Release and publish** (`api-utils==0.5.1`); **Standardized Get List pattern**
- `README.md`
- `Pipfile` / `Pipfile.lock` — currently pins `api-utils==0.5.0`

Additional inputs:

- `../mentorhub_api_utils/api_utils/services/resource_service.py` — `RESOURCE_LIST_FILTERS` on `0.5.1` / `main`
- `../mentorhub_api_utils/tasks/SHIPPED.R056.extend_resource_list_filters.md`
- `../mentorhub_api_utils/tasks/SHIPPED.R057.test_resource_list_multi_field_filters.md`
- `../mentorhub_api_utils/tasks/SHIPPED.R058.bump_patch_resource_list_filters.md`
- `tasks/ISSUE.mentorhub_api_utils.extend_resource_list_filters.md` — resolved handoff
- `tasks/SHIPPED.L180.bump_api_utils_0_5_0.md` — prior bump pattern
- `tasks/SHIPPED.L181.adopt_resource_list_get_list.md` — how this API consumes `RESOURCE_LIST_FILTERS`

**Upstream status**: Filter extension is implemented and merged (`api-utils` `0.5.1` on `main` via R056–R058).

**External prerequisite**: `api-utils==0.5.1` must be available on CodeArtifact (post-merge `tag-release`). Confirm it resolves with `pipenv run install` before starting. If it is not yet published, set **Status** to `Blocked` and stop. (Run `mh` first for CodeArtifact auth.)

Filter keys expected in `0.5.1`:

| Query param | Type | Field |
|-------------|------|-------|
| `url` | `contains` | `url` |
| `interests` | `in_list` | `interests` |
| `technologies` | `in_list` | `technologies` |
| `skill_level` | `in_list` | `skill_level` |

Existing `name` / `description` / `status` entries remain.

## Goals

- `Pipfile` pins `api-utils==0.5.1` (CodeArtifact index).
- `Pipfile.lock` updated via `pipenv run install`.
- Import / filter-spec check succeeds after install:
  ```python
  from api_utils.services.resource_service import RESOURCE_LIST_FILTERS
  assert set(RESOURCE_LIST_FILTERS) >= {
      "name", "description", "status",
      "url", "interests", "technologies", "skill_level",
  }
  ```
- No application code, OpenAPI, or test changes in this task — dependency bump only (docs/tests follow in L191–L192).

## Testing Expectations

Run all commands from the **API repository root**.

- **Install**
  - `pipenv run install` — resolves `api-utils==0.5.1` from CodeArtifact
  - Verify imports and filter keys (assert above)
- **Unit tests**
  - `pipenv run test` — existing suite still passes against `0.5.1` before L191–L192
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E suite still green on the bump alone

## Outputs

Paths are relative to the **API repository root**.

- `Pipfile` — bump `api-utils` version pin to `==0.5.1`
- `Pipfile.lock` — refreshed via `pipenv run install`

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
