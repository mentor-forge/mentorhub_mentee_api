# L150 – Implement PATCH /api/journey/complete/{resource_id} (now → library, aggregation, completed event)

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L140  
**Description**: Add `PATCH /api/journey/complete/{resource_id}` to move a resource from `now` to `library`, update Resource_Aggregation via `AggregationService.add_completion` (no event creation inside aggregation), and record a `completed` Event from the route/service layer.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — `PATCH /api/journey/complete/{resource_id}` and `JourneyCompleteInput` from L110
- `src/services/journey_service.py` — journey fetch, RBAC, advance patterns from L140
- `src/services/aggregation_service.py` — extend with `add_completion` per L050 spec (not present in current code)
- `src/services/event_service.py` — `create_event` with type `completed`
- `src/services/note_service.py` — optional note creation from `add_completion`
- `api_utils.Config` — `EVENT_TYPE_COMPLETED`, `ROLE_MENTEE`, `RESOURCE_AGGREGATION_COLLECTION_NAME`
- `tasks/SHIPPED.L050.aggregation_service_and_route.md` — `add_completion` design (mentee RBAC, counter increments, optional note; **no HTTP route**)
- `tasks/SHIPPED.T202.enhance_post_event_service.md` — events created at PATCH layer, not inside aggregation

Configurator schema:

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Resource_Aggregation.yaml/latest/" -H "accept: application/json"
```

Additional inputs:

- `test/services/test_aggregation_service.py` — add `add_completion` tests; confirm no event creation
- `test/services/test_journey_service.py`
- `test/routes/test_journey_routes.py`
- `test/e2e/test_journey.py` — optional complete scenario

**External prerequisite**: Mentee Journey `_id` equals `profile_id` and `resource_id` values are valid in seeded test data ([mentorhub_mongodb_api#45 — F-D19: resource_id test data](https://github.com/mentor-forge/mentorhub_mongodb_api/issues/45)). E2E complete scenarios against legacy data may be deferred; unit tests use mocks.

## Goals

- **`AggregationService.add_completion(resource_id, rating, note, duration, token, breadcrumb)`** (implement per L050; name kept as `add_completion`):
  - `_check_permission(token, 'add_completion')` — **mentee role** (`Config.ROLE_MENTEE` in token `roles`; `403` otherwise).
  - Get-or-create aggregation for `resource_id`.
  - Increment `completions`, `rating_count`, and `rating_sum` (when `rating` provided).
  - Add `duration` to aggregated `duration` (ISO 8601 duration arithmetic; default `PT0S` when omitted).
  - When `note` is provided, create Note via `NoteService.create_note` and increment `note_count`.
  - Update `last_saved` breadcrumb.
  - Return updated aggregation document.
  - **Must not** call `EventService` or create Event documents — remove any event-creation code if present.
- **`JourneyService.complete_resource(resource_id, data, token, breadcrumb)`**:
  - Load caller's journey (owner or admin RBAC).
  - Resolve `resource_id` path param to Resource document (by `_id`); map to `now` entry (match `now[].resource_id` against Resource `name` or `_id` per Journey schema conventions in test data).
  - If resource not in `now`, raise `HTTPNotFound`.
  - Build `library` entry: `resource_id` (`$oid` string), `started` (from `now` entry if present, else breadcrumb time), `completed` (breadcrumb time), `used` (from `now` or 0), optional `rating` from request body.
  - Remove entry from `now`; append to `library`.
  - Persist journey; update `saved`.
  - Call `AggregationService.add_completion` with `rating`, `note`, `duration` from optional request body (`JourneyCompleteInput`).
  - **Create Event**: `EventService.create_event` with `type` = `completed` (`Config.EVENT_TYPE_COMPLETED`); enrich token copy with `resource_id` and `journey_id`.
  - Return updated Journey.
- **`journey_routes.py`**:
  - `PATCH "/complete/<resource_id>"` — optional JSON body; call `complete_resource`; return `200` + Journey.
  - Register before `PATCH "/<journey_id>"`.
- **Unit tests**:
  - `test/services/test_aggregation_service.py` — `add_completion` increments counters; mentee RBAC; **no** `EventService` calls (mock and assert not called).
  - `test/services/test_journey_service.py` — complete moves `now` → `library`; calls `add_completion` and `create_event` exactly once each.
  - `test/routes/test_journey_routes.py` — complete route success and error paths.
- **E2E** (optional): complete a resource in `now` on a test journey; verify `library` growth and aggregation counters.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_aggregation_service.py` — `add_completion` without events
  - `test/services/test_journey_service.py` — complete flow
  - `test/routes/test_journey_routes.py` — complete route
- **Build**
  - `pipenv run build`
- **Dev E2E**
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - `test/e2e/test_journey.py` — complete scenario when test data allows
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e` against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/services/aggregation_service.py` — `add_completion` (no event creation)
- `src/services/journey_service.py` — `complete_resource`
- `src/routes/journey_routes.py` — `PATCH /api/journey/complete/<resource_id>`
- `test/services/test_aggregation_service.py` — `add_completion` tests
- `test/services/test_journey_service.py` — complete unit tests
- `test/routes/test_journey_routes.py` — complete route tests
- `test/e2e/test_journey.py` — optional complete E2E

The agent must not update files outside this list.

## Execution Notes

**Summary**
- Added `PATCH /api/journey/complete/<resource_id>` and `JourneyService.complete_resource`.
- Implemented `AggregationService.add_completion` (mentee RBAC, no events).
- Complete flow creates `completed` event at PATCH layer.

**Testing**
- `pipenv run test`: 96 passed including add_completion and complete tests.
- `pipenv run container`: image built successfully.
