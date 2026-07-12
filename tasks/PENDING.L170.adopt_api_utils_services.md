# L170 – Adopt shared api_utils services and remove local copies

**Status**: Pending  
**Type**: Feature  
**Depends On**: `L160_bump_api_utils_0_4_0`  
**Description**: Delete duplicate domain service modules under `src/services/` and switch routes and tests to import service classes from `api_utils.services` (or top-level `api_utils`).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `../mentorhub_api_utils/api_utils/services/__init__.py` — public service exports
- `../mentorhub_api_utils/api_utils/__init__.py` — top-level re-exports
- `README.md`
- `Pipfile` — must already pin `api-utils==0.4.0` (L160)

**Local services to remove** (harvested to `api_utils.services` in api_utils R041–R047):

| Local file | Replacement import |
|------------|-------------------|
| `src/services/note_service.py` | `from api_utils.services import NoteService` |
| `src/services/aggregation_service.py` | `from api_utils.services import AggregationService` |
| `src/services/event_service.py` | `from api_utils.services import EventService` |
| `src/services/resource_service.py` | `from api_utils.services import ResourceService` |
| `src/services/path_service.py` | `from api_utils.services import PathService` |
| `src/services/journey_service.py` | `from api_utils.services import JourneyService, TEMPLATE_JOURNEY_ID` |

Preferred import style (match existing `api_utils` usage in routes):

```python
from api_utils.services import JourneyService
# or
from api_utils import JourneyService
```

Use one style consistently across all route modules in this task.

**Duplicate unit tests**: Service unit tests were ported to `../mentorhub_api_utils/tests/services/` during harvest. Remove the mentee API copies under `test/services/test_*_service.py` rather than re-pointing them — route and E2E tests remain the integration coverage for this API.

**External prerequisite**: L160 complete and `api-utils==0.4.0` installed. If service imports fail or behavior diverges from the local copies, set **Status** to `Blocked` and document the gap in **Execution Notes** — do not keep partial local service files.

## Goals

- All six local service modules and `src/services/__init__.py` are **deleted**; the `src/services/` directory is removed when empty.
- Route modules import service classes from `api_utils.services` (or `api_utils`) instead of `src.services`:
  - `src/routes/aggregation_routes.py`
  - `src/routes/event_routes.py`
  - `src/routes/journey_routes.py`
  - `src/routes/note_routes.py`
  - `src/routes/path_routes.py`
  - `src/routes/resource_routes.py`
- Duplicate service unit tests under `test/services/test_*_service.py` are **deleted** (coverage lives in api_utils).
- Route unit tests continue to pass — `@patch` targets remain on the route module namespace (e.g. `src.routes.journey_routes.JourneyService.*`) after the import change.
- No remaining references to `src.services` anywhere in `src/` or `test/`.
- `README.md` — if it mentions maintaining local `src/services/` copies, update to note services come from `api-utils`.

## Testing Expectations

Run all commands from the **API repository root**.

- **Install** (confirm L160 pin still resolves)
  - `pipenv run install`
- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - Route tests: `test/routes/test_aggregation_routes.py`, `test/routes/test_event_routes.py`, `test/routes/test_journey_routes.py`, `test/routes/test_note_routes.py`, `test/routes/test_path_routes.py`, `test/routes/test_resource_routes.py`
  - `test/test_server.py`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e`
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API

## Outputs

**Delete**

- `src/services/note_service.py`
- `src/services/aggregation_service.py`
- `src/services/event_service.py`
- `src/services/resource_service.py`
- `src/services/path_service.py`
- `src/services/journey_service.py`
- `src/services/__init__.py`
- `test/services/test_note_service.py`
- `test/services/test_aggregation_service.py`
- `test/services/test_event_service.py`
- `test/services/test_resource_service.py`
- `test/services/test_path_service.py`
- `test/services/test_journey_service.py`

**Update**

- `src/routes/aggregation_routes.py` — import `AggregationService` from `api_utils.services`
- `src/routes/event_routes.py` — import `EventService` from `api_utils.services`
- `src/routes/journey_routes.py` — import `JourneyService` from `api_utils.services`
- `src/routes/note_routes.py` — import `NoteService` from `api_utils.services`
- `src/routes/path_routes.py` — import `PathService` from `api_utils.services`
- `src/routes/resource_routes.py` — import `ResourceService` from `api_utils.services`
- `README.md` — document that domain services are provided by `api-utils`, not local `src/services/`

The agent must not update files outside this list unless a stray `src.services` reference is discovered in `src/` or `test/` during implementation — in that case, add the file to **Execution Notes** and update it in the same commit.

## Execution Notes

_Reserved for the task execution agent._
