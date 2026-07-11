# T200 – Update OpenAPI for POST Event schema

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Fetch the latest `Event` JSON schema from the MongoDB configurator and update `docs/openapi.yaml`: sync `Event` and `EventInput` component schemas to the current MongoDB dictionary. The mentee API remains **POST-only** for events — do not add `GET /api/event`. Event `context` is **server-populated from the JWT token** (all token properties); clients send only `type`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — current POST-only Event contract from L040/L060
- `tasks/SHIPPED.L040.cleanup_openapi_aggregation_note_event.md` — prior Event OpenAPI cleanup
- `tasks/SHIPPED.L060.simplify_note_event_endpoints.md` — runtime and contract are POST-only; mentee UI posts events only (no list/read)
- `../mentorhub_api_utils/api_utils/flask_utils/token.py` — `create_flask_token` / `Token.to_dict()`; token shape may evolve

Additional inputs:

- Latest schema from the MongoDB configurator (configurator API on port `8383`; start with `pipenv run db` if needed):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Event.yaml/latest/" -H "accept: application/json"
```

- `src/routes/event_routes.py` — POST-only runtime today
- `src/services/event_service.py` — `create_event` / `get_event` only

**External prerequisite**: MongoDB configurator is running and serves the current `Event` dictionary schema at the URL above. If the configurator is unavailable, try `pipenv run db`; if the API call still fails, set **Status** to `Blocked` and stop.

## Goals

- **`Event` component schema** in `docs/openapi.yaml` matches the latest configurator JSON schema:
  - `type` enum values aligned with `event_types` enumerator.
  - `context` object with `additionalProperties: true` and documented identifier properties from the dictionary and token usage (`profile_id`, `resource_id`, `journey_id`, `user_id`, `customer_id`, `mentor_id`, etc. as optional properties).
  - `created` breadcrumb schema unchanged.
  - Document in `context` description that values are populated server-side from the authenticated JWT token (see T202); not supplied by the client.
- **`EventInput` component schema** matches the create payload shape:
  - Required: `type` only.
  - **No `context` property** on input — context is derived from the token at create time so future token claim changes do not require API contract or client changes.
  - No `created` or `_id` on input (system-managed).
- **`POST /api/event`** documented with:
  - `EventInput` request body (`type` only).
  - `Event` response including server-populated `context`.
  - Operation description states that `context` is built from all JWT token properties (`create_flask_token` / `Token.to_dict()`); the client does not send context fields.
- **Do not** add `GET /api/event` or any other Event read/list operations — the mentee UI only posts events.
- Update the `Event` tag description to reflect create-only semantics and token-sourced context.
- OpenAPI path casing matches runtime routes: lowercase `/api/event`.
- The spec parses, every `$ref` resolves, and the API serves it at `/docs/openapi.yaml`.

## Testing Expectations

This is a documentation/contract task; validate the spec rather than runtime behavior (T202 implements POST enhancements).

Run all commands from the **API repository root**.

- **Spec validation**
  - Parses: `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - No dangling `$ref`s — every `$ref` resolves to a defined component.
  - Confirm only `POST /api/event` is documented (no `GET` list or detail paths).
  - Confirm `EventInput` has only `type` (no `context` property).
  - Confirm `Event.context` documents token-sourced fields and `additionalProperties: true`.
- **Lint**
  - `pipenv run lint`
- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - Verify the spec is served: `curl -s http://localhost:8393/docs/openapi.yaml | head`
  - Optionally render in the Swagger explorer (`pipenv run dev` → `/docs`).

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — sync `Event` and `EventInput` schemas to MongoDB dictionary; POST-only Event contract with token-sourced context

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
