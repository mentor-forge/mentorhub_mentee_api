# L140 – Implement PATCH /api/journey/advance/{resource_id} (next → now, advanced event)

**Status**: Pending  
**Type**: Feature  
**Depends On**: L130  
**Description**: Add `PATCH /api/journey/advance/{resource_id}` to move a resource from the Journey `next` scope into `now` by Resource ID, and record an `advanced` Event via `EventService` (not via aggregation helpers).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — `PATCH /api/journey/advance/{resource_id}` from L110
- `src/services/journey_service.py` — `get_my_journey`, RBAC from L130
- `src/services/event_service.py` — `create_event` (context from token; type `advanced`)
- `src/routes/journey_routes.py`
- `api_utils.Config` — `EVENT_COLLECTION_NAME`, `EVENT_TYPE_ADVANCED`, `RESOURCE_COLLECTION_NAME`, `JOURNEY_COLLECTION_NAME`
- `tasks/SHIPPED.T202.enhance_post_event_service.md` — event context populated from token
- MongoDB Journey test data shape — `now.resource_id` uses Resource **`name`** (word); `next` modules/topics hold Resource `$oid` values (T117/T118)

Additional inputs:

- `test/services/test_journey_service.py`
- `test/routes/test_journey_routes.py`
- `test/e2e/test_journey.py` — optional advance scenario

**External prerequisites**:

- Resource documents referenced in template Journey `next` scope exist in test data (MongoDB T116/T117).
- Mentee Journey `_id` equals `profile_id` and all `resource_id` values are valid Resource `$oid` references in seeded test data ([mentorhub_mongodb_api#45 — F-D19: resource_id test data](https://github.com/mentor-forge/mentorhub_mongodb_api/issues/45)). E2E advance scenarios against legacy data may be skipped or deferred until that issue ships; unit tests use mocks.

## Goals

- **`JourneyService.advance_resource(resource_id, token, breadcrumb)`**:
  - Resolve the caller's journey via `get_my_journey` (or equivalent internal fetch by `profile_id`).
  - Enforce ownership RBAC (same rule as PATCH update: owner or admin).
  - Validate `resource_id` as a MongoDB ObjectId; load Resource by `_id` via `MongoIO.get_document` (or Resource service helper). Raise `HTTPNotFound` when the Resource does not exist.
  - Locate the resource in `journey.next` (walk modules → topics → `resources` identifier list). Match by Resource `_id` string.
  - If not found in `next`, raise `HTTPNotFound` (or `HTTPBadRequest` with a clear message).
  - Remove the resource from `next` (prune empty topics/modules as needed).
  - Append to `now[]` with `resource_id` = Resource **`name`**, `added` = breadcrumb `at_time`, `used` = 0 (and `started` omitted until link event).
  - Persist via `MongoIO.update_document`; update `saved` breadcrumb.
  - **Create Event**: call `EventService.create_event` with `type` = `advanced` (`Config.EVENT_TYPE_ADVANCED`). Merge `resource_id` and `journey_id` (= token `profile_id`) into the token dict passed to event creation so `context` captures them.
  - Return the updated Journey document.
  - **Do not** call `AggregationService` from this flow.
- **`journey_routes.py`**:
  - `PATCH "/advance/<resource_id>"` — call `advance_resource`; return `200` + Journey (no request body).
  - Register this route **before** `PATCH "/<journey_id>"` to avoid path conflicts.
- **Unit tests**:
  - Successful advance moves resource from `next` to `now`; `EventService.create_event` called once with type `advanced`.
  - Unknown `resource_id` (no Resource document) → `404`.
  - Resource not in `next` → `404` or `400`.
  - Invalid `resource_id` format → `400`.
  - Non-owner non-admin → `403`.
- **Route tests** for `PATCH /api/journey/advance/{resource_id}`.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_journey_service.py` — advance logic and event creation
  - `test/routes/test_journey_routes.py` — advance route
- **Build**
  - `pipenv run build`
- **Dev E2E** (when test data supports `_id` == `profile_id` alignment)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/journey_service.py` — `advance_resource`
- `src/routes/journey_routes.py` — `PATCH /api/journey/advance/<resource_id>`
- `test/services/test_journey_service.py` — advance unit tests
- `test/routes/test_journey_routes.py` — advance route tests
- `test/e2e/test_journey.py` — optional advance E2E scenario

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
