# L160 – Bump api-utils to 0.4.0

**Status**: Shipped  
**Type**: Feature  
**Depends On**: none  
**Description**: Pin `api-utils==0.4.0` in the Pipfile and refresh the lockfile so this API resolves the published package that exports shared domain services from `api_utils.services`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `Pipfile` / `Pipfile.lock` — currently pins `api-utils==0.3.0`

**External prerequisite**: `api-utils==0.4.0` must be published to CodeArtifact with the harvested service classes (`NoteService`, `AggregationService`, `EventService`, `ResourceService`, `PathService`, `JourneyService`, and `TEMPLATE_JOURNEY_ID`) exported from `api_utils.services` and the top-level `api_utils` package. Confirm the version resolves with `pipenv run install` before starting. If it is not yet available, set **Status** to `Blocked` and stop. (Run `mh` first for CodeArtifact auth.)

## Goals

- `Pipfile` pins `api-utils==0.4.0` (CodeArtifact index).
- `Pipfile.lock` updated via `pipenv run install`.
- `python -c "from api_utils import JourneyService, PathService; print(JourneyService, PathService)"` succeeds in the project venv after install.
- No application code changes in this task — dependency bump only.

## Testing Expectations

Run all commands from the **API repository root**.

- **Install**
  - `pipenv run install` — resolves `api-utils==0.4.0` from CodeArtifact
  - Verify import: `pipenv run python -c "from api_utils import JourneyService, AggregationService, EventService, NoteService, PathService, ResourceService, TEMPLATE_JOURNEY_ID"`
- **Unit tests**
  - `pipenv run test` — existing suite still passes against 0.4.0 (local `src/services/` copies remain until L170)
  - `pipenv run lint`
- **Build**
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API

## Outputs

- `Pipfile` — bump `api-utils` version pin to `==0.4.0`
- `Pipfile.lock` — refreshed lockfile from `pipenv run install`

The agent must not update files outside this list.

## Execution Notes

**Shipped (2026-07-12).** Bumped `Pipfile` pin from `api-utils==0.3.0` to `==0.4.0` and regenerated `Pipfile.lock` via `pipenv lock` + `pipenv run install`.

**Test results**
- Import check: all six service classes and `TEMPLATE_JOURNEY_ID` resolve from `api_utils`
- `pipenv run test`: 96 passed
- `pipenv run lint`: pass
- `pipenv run build`: pass
- `pipenv run container`: pass (image builds with `api-utils==0.4.0`)
- `pipenv run api` + `pipenv run e2e`: 19 passed
