# L200 – Bump api-utils to 0.5.2 for Journey harvest

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Pin and install `api-utils==0.5.2` so `JourneyService` exposes promote mutations and GET profile enrichment needed for L201.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md` — **Release and publish** (`api-utils==0.5.2`)
- `README.md`
- `Pipfile` / `Pipfile.lock` — currently pins `api-utils==0.5.1`

Additional inputs:

- `../mentorhub_api_utils/api_utils/services/journey_service.py` — `get_my_journey_detail`, `promote_path_to_next`, `promote_module_to_next`, `"profile"` in `RESTRICTED_UPDATE_FIELDS`
- `tasks/SHIPPED.L190.bump_api_utils_resource_list_filters.md` — prior bump pattern

**External prerequisite**: `api-utils==0.5.2` is published to CodeArtifact. Confirm it resolves with `pipenv run install` before starting. (Run `mh` first for CodeArtifact auth if credentials are not already available.)

Methods expected on `JourneyService` in `0.5.2`:

| Method | Purpose |
|--------|---------|
| `get_my_journey_detail` | GET `/api/journey` — Journey + embedded `profile` |
| `promote_path_to_next` | PATCH promote path |
| `promote_module_to_next` | PATCH promote module |

`RESTRICTED_UPDATE_FIELDS` must include `"profile"` (service-layer PATCH guard for L201).

## Goals

- `Pipfile` pins `api-utils==0.5.2` (CodeArtifact index).
- `Pipfile.lock` updated via `pipenv run install`.
- Import check succeeds after install:
  ```python
  from api_utils.services.journey_service import JourneyService, RESTRICTED_UPDATE_FIELDS

  assert "profile" in RESTRICTED_UPDATE_FIELDS
  assert callable(JourneyService.get_my_journey_detail)
  assert callable(JourneyService.promote_path_to_next)
  assert callable(JourneyService.promote_module_to_next)
  ```
- No application code, route, test, or OpenAPI changes in this task — dependency bump only (adoption follows in L201).

## Testing Expectations

Run all commands from the **API repository root**.

- **Install**
  - `pipenv run install` — resolves `api-utils==0.5.2` from CodeArtifact
  - Verify imports and methods (assert above)
- **Unit tests**
  - `pipenv run test` — existing suite still passes against `0.5.2` before L201 route adoption
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E suite still green on the bump alone

## Outputs

Paths are relative to the **API repository root**.

- `Pipfile` — bump `api-utils` version pin to `==0.5.2`
- `Pipfile.lock` — refreshed via `pipenv run install`

The agent must not update files outside this list.

## Execution Notes
