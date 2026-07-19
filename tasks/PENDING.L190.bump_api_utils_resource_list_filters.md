# L190 – Bump api-utils for Resource list multi-field filters

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Pin and install the published `api-utils` release that extends `RESOURCE_LIST_FILTERS` with `url`, `interests`, `technologies`, and `skill_level`, so `parse_list_request` on `GET /api/resource` accepts those query params without route-layer filter wiring changes.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md` — **Standardized Get List pattern**
- `README.md`
- `Pipfile` / `Pipfile.lock` — currently pins `api-utils==0.5.0`

Additional inputs:

- `../mentorhub_api_utils/api_utils/services/resource_service.py` — `RESOURCE_LIST_FILTERS` (source of truth after the upstream change)
- `tasks/ISSUE.mentorhub_api_utils.extend_resource_list_filters.md` — upstream handoff
- `tasks/SHIPPED.L180.bump_api_utils_0_5_0.md` — prior bump pattern
- `tasks/SHIPPED.L181.adopt_resource_list_get_list.md` — how this API consumes `RESOURCE_LIST_FILTERS`

**External prerequisite**: `api-utils` must be published to CodeArtifact with `RESOURCE_LIST_FILTERS` extended as:

| Query param | Type | Field |
|-------------|------|-------|
| `url` | `contains` | `url` |
| `interests` | `in_list` | `interests` |
| `technologies` | `in_list` | `technologies` |
| `skill_level` | `in_list` | `skill_level` |

Existing `name` / `description` / `status` entries must remain. Confirm the new version resolves with `pipenv run install` before starting. If it is not yet available, set **Status** to `Blocked` and stop. (Run `mh` first for CodeArtifact auth.)

Use the published version number from the upstream release (expected patch such as `0.5.1` — replace with the actual published version).

## Goals

- `Pipfile` pins `api-utils` to the published version that includes the new Resource list filters (CodeArtifact index).
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
  - `pipenv run install` — resolves the new `api-utils` from CodeArtifact
  - Verify imports and filter keys (assert above)
- **Unit tests**
  - `pipenv run test` — existing suite still passes against the new pin before L191–L192
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E suite still green on the bump alone

## Outputs

Paths are relative to the **API repository root**.

- `Pipfile` — bump `api-utils` version pin to the published release that includes the new filters
- `Pipfile.lock` — refreshed via `pipenv run install`

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
