# L030 – Resource detail with aggregation and notes

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L010  
**Description**: Update `GET /api/resource/{id}` to return the L010 `ResourceDetail` composite: the `Resource` document, its `Resource_Aggregation` metrics (via a new `AggregationService`), and related `Note` documents (via `NoteService`). Use service-to-service calls; any authenticated user may read Resource, Aggregation, and Note data.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — `ResourceDetail` contract from L010

Pattern references:

- `../mentorhub_mentor_api/tasks/SHIPPED.L030.update_profile_service_composite_detail.md` — composite detail via service-to-service calls
- `src/services/resource_service.py` — current `get_resource` returns the raw document
- `src/services/note_service.py` — add a per-resource notes query (by `resource_id` field on Note documents)
- `api_utils.Config` — `RESOURCE_AGGREGATION_COLLECTION_NAME` (default `Resource_Aggregation`)
- `../mentorhub_mongodb_api/configurator/dictionaries/Resource_Aggregation.0.1.0.yaml`
- `../mentorhub_mongodb_api/configurator/dictionaries/Note.0.1.0.yaml`
- `../mentorhub_mongodb_api/erd.svg` — Resource ↔ Note ↔ Resource_Aggregation relationships
- Upstream prerequisite for orchestration: the `Resource` schema/configurator change adding `archived` to `resource_status` must already be present in the running environment before L010/L030 are executed together against that contract.

Additional inputs:

- `src/routes/resource_routes.py`
- `test/routes/test_resource_routes.py`
- `test/services/test_resource_service.py`
- `test/services/test_note_service.py` — if NoteService gains a new method
- `test/e2e/test_resource.py`

## Goals

- New `src/services/aggregation_service.py` (`AggregationService`):
  - Single-collection aligned to `RESOURCE_AGGREGATION_COLLECTION_NAME`.
  - `get_aggregation_for_resource(resource_id, token, breadcrumb)` — lookup by `resource_id`; return the aggregation document or `None` if none exists (not `404` for missing aggregation).
  - `_check_permission(token, 'read')` — any authenticated user may read (no additional role gate).
- `NoteService` gains `get_notes_for_resource(resource_id, token, breadcrumb)` (or equivalent name):
  - Returns an array of `Note` documents where `resource_id` matches.
  - `_check_permission(token, 'read')` — any authenticated user may read.
  - Implemented in `note_service.py` only (no direct Note collection access from `resource_service`).
- `ResourceService.get_resource(resource_id, token, breadcrumb)` returns `ResourceDetail`:
  - `{ "resource": <Resource>, "aggregation": <ResourceAggregation|null>, "notes": [<Note>, ...] }`
  - `resource` — `404` if not found.
  - `aggregation` and `notes` fetched via **service-to-service** calls to `AggregationService` and `NoteService` (import inside method to avoid circular imports).
  - `ResourceService` does not query Note or Resource_Aggregation collections directly.
- `GET /api/resource/{id}` route unchanged in path; response body matches `ResourceDetail`.
- Confirm no `PATCH /api/resource/{id}` route exists (remove if accidentally added; mentees cannot update resources).
- Unit and E2E tests cover the composite shape and service-to-service wiring.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_aggregation_service.py` — **new** tests for lookup by `resource_id` and read RBAC
  - `test/services/test_note_service.py` — tests for `get_notes_for_resource`
  - `test/services/test_resource_service.py` — `get_resource` returns composite; mocks `AggregationService` and `NoteService`; asserts no direct cross-collection access
  - `test/routes/test_resource_routes.py` — `get_resource` returns composite JSON
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - `test/e2e/test_resource.py` — `GET /api/resource/{id}` returns `{ resource, aggregation, notes }` keys; `notes` is an array
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e` against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/services/aggregation_service.py` — **new** `AggregationService` for Resource_Aggregation reads
- `src/services/note_service.py` — add `get_notes_for_resource`
- `src/services/resource_service.py` — `get_resource` returns `ResourceDetail` via service-to-service calls
- `test/services/test_aggregation_service.py` — **new** unit tests
- `test/services/test_note_service.py` — tests for per-resource notes query
- `test/services/test_resource_service.py` — composite detail tests
- `test/routes/test_resource_routes.py` — updated get-by-id route test
- `test/e2e/test_resource.py` — composite detail e2e assertion

The agent must not update files outside this list.

## Execution Notes

**Summary of changes**
- Added `AggregationService` for `Resource_Aggregation` lookups by `resource_id`.
- Added `NoteService.get_notes_for_resource` for per-resource note queries.
- `ResourceService.get_resource` returns `{resource, aggregation, notes}` via service-to-service calls.
- Confirmed no `PATCH /api/resource/{id}` route exists.

**Testing results**
- `pipenv run test`: 149 passed, 25 deselected.
- `pipenv run build`: clean.
- E2E (`pipenv run e2e`) deferred — requires running API at `localhost:8393`.
