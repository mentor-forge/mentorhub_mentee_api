# T202 – Enhance POST event: token-sourced context and link hit aggregation

**Status**: Pending  
**Type**: Feature  
**Depends On**: T200  
**Description**: Update `EventService.create_event` to populate `context` entirely from the JWT token dict (all properties, no hard-coded field list), align create encoding with the updated Event MongoDB schema, and call `AggregationService.add_hit` when posting a `link` event whose token context includes `resource_id`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — updated `Event` / `EventInput` schemas from T200
- `api_utils/flask_utils/token.py` — `create_flask_token` / `Token.to_dict()`; token shape may evolve (do not enumerate fields in POST logic)
- `src/services/event_service.py` — current `create_event` implementation
- `src/services/aggregation_service.py` — `add_hit(resource_id, token, breadcrumb)` from L050
- `tasks/SHIPPED.L050.aggregation_service_and_route.md` — `add_hit` reserved for POST Event link integration
- `tasks/SHIPPED.L060.simplify_note_event_endpoints.md` — POST-only Event route surface

Additional inputs:

- `src/routes/event_routes.py` — POST handler (should remain thin; logic in service)
- `test/services/test_event_service.py`
- `test/routes/test_event_routes.py`
- `test/e2e/test_event.py`
- `test/services/test_aggregation_service.py` — `add_hit` behavior reference

Latest Event schema from configurator (start `pipenv run db` if needed):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Event.yaml/latest/" -H "accept: application/json"
```

MongoDB access: use `MongoIO.create_document` only — no direct PyMongo calls.

## Goals

- **Token → context (forward-compatible)**:
  - In `EventService.create_event`, set `context` from the full `token` dict — all token properties, not a hand-picked subset:
    - Example approach: `data["context"] = dict(token)` (or equivalent shallow copy).
  - Do **not** read `context` from the request body; ignore or strip any client-supplied `context` so the API payload cannot override token values.
  - Do **not** hard-code individual token keys (e.g. do not special-case only `profile_id` or `user_id`); new token fields must flow into `context` automatically when `Token.to_dict()` / JWT claims expand.
- **MongoDB schema alignment on create**:
  - Extend `ID_PROPERTIES` (and any related encoding lists) so nested `context` identifier fields used by the Event dictionary are encoded to BSON ObjectId via `encode_document` (at minimum `profile_id`; include `resource_id`, `journey_id`, and other identifier properties documented in T200 / configurator schema).
  - Ensure create payloads match the updated `EventInput` OpenAPI contract (required `type` only; no client `context`, `created`, or `_id`).
- **`link` event → aggregation hit**:
  - After successfully creating an event where `type == "link"`, call `AggregationService.add_hit(resource_id, token, breadcrumb)` when the token-sourced `context` contains a `resource_id`.
  - Import `AggregationService` inside `create_event` (or at module level) following the service-to-service pattern used elsewhere; avoid circular imports.
  - If `type == "link"` but `resource_id` is missing from token/context, still create the event; skip `add_hit` and log at info/warning (do not fail the POST).
  - Non-`link` event types must not call `add_hit`.
- **Tests**:
  - `test/services/test_event_service.py`:
    - Assert `context` includes all keys from a mock token dict without listing them individually in production code.
    - Assert client-supplied `context` in the request body is ignored (not merged).
    - Assert `link` event with `resource_id` in token invokes `AggregationService.add_hit` (mock aggregation service).
    - Assert non-`link` events do not call `add_hit`.
    - Assert `link` without `resource_id` in token still creates event and does not call `add_hit`.
  - `test/e2e/test_event.py` — POST `link` event (body: `type` only); verify created `context` matches token fields; optional follow-up `GET /api/aggregation/{resource_id}` to confirm `hits` incremented when E2E token/data includes `resource_id`.
- `pipenv run test`, `pipenv run lint`, and `pipenv run build` pass.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_event_service.py` — token-sourced context, encoding, `add_hit` integration
  - `test/routes/test_event_routes.py` — POST still returns created document (201)
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e`
  - `test/e2e/test_event.py` — POST `link` with `type` only; verify created `context` reflects token fields
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/services/event_service.py` — token-sourced context, identifier encoding, `add_hit` on `link` events
- `test/services/test_event_service.py` — create_event token context and aggregation tests
- `test/e2e/test_event.py` — POST link event and context assertions

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
