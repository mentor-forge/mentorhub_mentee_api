# T202 – Enhance POST event: token context merge and link hit aggregation

**Status**: Pending  
**Type**: Feature  
**Depends On**: T201  
**Description**: Update `EventService.create_event` to merge all JWT token claims into `context` without hard-coding individual fields, align create payload encoding with the updated Event MongoDB schema, and call `AggregationService.add_hit` when posting a `link` event.

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

- **Token → context merge (forward-compatible)**:
  - In `EventService.create_event`, build `context` by shallow-merging the full `token` dict with any client-supplied `context` from the request body, with **client values overriding token values** on key collision:
    - Example approach: `context = {**token, **(data.get("context") or {})}` then assign `data["context"] = context`.
  - Do **not** hard-code individual token keys (e.g. do not special-case only `profile_id` or `user_id`); new token fields must flow into `context` automatically when `Token.to_dict()` / JWT claims expand.
  - Preserve existing behavior where the client may supply `profile_id`, `resource_id`, `journey_id`, etc. in `context`; client-supplied values win over token defaults.
- **MongoDB schema alignment on create**:
  - Extend `ID_PROPERTIES` (and any related encoding lists) so nested `context` identifier fields used by the Event dictionary are encoded to BSON ObjectId via `encode_document` (at minimum `profile_id`; include `resource_id`, `journey_id`, and other identifier properties documented in T200 / configurator schema).
  - Ensure create payloads match the updated `EventInput` OpenAPI contract (required `type`, optional `context`, no client `created` / `_id`).
- **`link` event → aggregation hit**:
  - After successfully creating an event where `type == "link"`, call `AggregationService.add_hit(resource_id, token, breadcrumb)` when `context` contains a `resource_id`.
  - Import `AggregationService` inside `create_event` (or at module level) following the service-to-service pattern used elsewhere; avoid circular imports.
  - If `type == "link"` but `resource_id` is missing from `context`, still create the event; skip `add_hit` and log at info/warning (do not fail the POST).
  - Non-`link` event types must not call `add_hit`.
- **Tests**:
  - `test/services/test_event_service.py`:
    - Assert merged `context` includes all keys from a mock token dict without listing them individually in production code.
    - Assert client `context` overrides token values on collision.
    - Assert `link` event with `resource_id` invokes `AggregationService.add_hit` (mock aggregation service).
    - Assert non-`link` events do not call `add_hit`.
    - Assert `link` without `resource_id` still creates event and does not call `add_hit`.
  - `test/e2e/test_event.py` — POST `link` event with `resource_id`; optional follow-up `GET /api/aggregation/{resource_id}` to confirm `hits` incremented when E2E data supports it.
- `pipenv run test`, `pipenv run lint`, and `pipenv run build` pass.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_event_service.py` — token merge, encoding, `add_hit` integration
  - `test/routes/test_event_routes.py` — POST still returns created document (201)
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e`
  - `test/e2e/test_event.py` — POST `link` with `resource_id`; verify created `context` includes token fields
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/services/event_service.py` — token-context merge, identifier encoding, `add_hit` on `link` events
- `test/services/test_event_service.py` — create_event token merge and aggregation tests
- `test/e2e/test_event.py` — POST link event and context assertions

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
