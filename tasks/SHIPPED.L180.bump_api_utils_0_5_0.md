# L180 – Bump api-utils to 0.5.0

**Status**: Shipped  
**Type**: Feature  
**Depends On**: none  
**Description**: Pin `api-utils==0.5.0` in the Pipfile and refresh the lockfile so this API resolves the published package with standardized Get List utilities (`parse_list_request`, paginated `PathService.get_paths`, filter/sort support on `ResourceService.get_resources`, and composite full-note fetch via `NoteService.list_all_notes_for_resource`).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md` — **Standardized Get List pattern** section
- `README.md`
- `Pipfile` / `Pipfile.lock` — currently pins `api-utils==0.4.0`

**External prerequisite**: `api-utils==0.5.0` must be published to CodeArtifact with R048–R054 shipped (`list_query`, `list_request`, refactored `ResourceService.get_resources`, paginated `PathService.get_paths`, paginated `NoteService.get_notes_for_resource` with `list_all_notes_for_resource` for composites). Confirm the version resolves with `pipenv run install` before starting. If it is not yet available, set **Status** to `Blocked` and stop. (Run `mh` first for CodeArtifact auth.)

Reference: `../mentorhub_api_utils/tasks/_PLANNING.md` — **Downstream follow-on issues → mentorhub_mentee_api**.

## Goals

- `Pipfile` pins `api-utils==0.5.0` (CodeArtifact index).
- `Pipfile.lock` updated via `pipenv run install`.
- Import check succeeds after install:
  - `from api_utils.flask_utils.list_request import parse_list_request`
  - `from api_utils.services.resource_service import RESOURCE_LIST_FILTERS, RESOURCE_LIST_ORDER`
  - `from api_utils.services.path_service import PATH_LIST_FILTERS, PATH_LIST_ORDER`
  - `from api_utils.services import ResourceService, PathService, NoteService, AggregationService`
- No application code changes in this task — dependency bump only.

## Testing Expectations

Run all commands from the **API repository root**.

- **Install**
  - `pipenv run install` — resolves `api-utils==0.5.0` from CodeArtifact
  - Verify imports:
    ```bash
    pipenv run python -c "
    from api_utils.flask_utils.list_request import parse_list_request
    from api_utils.services.resource_service import RESOURCE_LIST_FILTERS, RESOURCE_LIST_ORDER
    from api_utils.services.path_service import PATH_LIST_FILTERS, PATH_LIST_ORDER
    from api_utils.services import ResourceService, PathService, NoteService
    print('ok')
    "
    ```
- **Unit tests**
  - `pipenv run test` — existing suite still passes against 0.5.0 before route-layer adoption (L181–L184)
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API

## Outputs

- `Pipfile` — bump `api-utils` version pin to `==0.5.0`
- `Pipfile.lock` — refreshed lockfile from `pipenv run install`

The agent must not update files outside this list.

## Execution Notes

**Summary of changes**
- Bumped `Pipfile` pin from `api-utils==0.4.0` to `==0.5.0`.
- Updated `Pipfile.lock` with 0.5.0 hash; installed via CodeArtifact mirror.

**Test results**
- Import check: `parse_list_request`, `RESOURCE_LIST_*`, `PATH_LIST_*`, service classes — ok
- `pipenv run test`: 41 passed
- `pipenv run lint`: pass
- `pipenv run build`: pass
- `pipenv run container`: pass
- `pipenv run api` + `pipenv run e2e`: 19 passed
