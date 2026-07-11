# T200 – Update OpenAPI for Event list and POST schema

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Fetch the latest `Event` JSON schema from the MongoDB configurator and update `docs/openapi.yaml`: add `GET /api/event` with offset/size request-header pagination returning a plain array; sync `Event` and `EventInput` component schemas to the current MongoDB dictionary (including `context` identifier fields used in test data).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — current POST-only Event contract from L040/L060
- `tasks/SHIPPED.L040.cleanup_openapi_aggregation_note_event.md` — prior Event OpenAPI cleanup
- `tasks/SHIPPED.L060.simplify_note_event_endpoints.md` — runtime is POST-only today; this task restores list read in the contract
- `tasks/SHIPPED.L010.update_resource_openapi.md` — offset/size header pagination pattern reference
- `tasks/SHIPPED.L020.simplify_resource_list_pagination.md` — list implementation pattern reference

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
  - `context` object with `additionalProperties: true` and documented identifier properties from the dictionary and realistic test-data usage (`profile_id`, `resource_id`, `journey_id` as optional `$ref` or inline identifier patterns).
  - `created` breadcrumb schema unchanged.
- **`EventInput` component schema** matches the create payload shape:
  - Required: `type`.
  - Optional: `context` (same shape as `Event.context`; client may supply `profile_id`, `resource_id`, `journey_id`, etc.).
  - No `created` or `_id` on input (system-managed).
- **`GET /api/event`** documented as:
  - Returns `200` with a **JSON array** of `Event` objects (no infinite-scroll wrapper such as `items` / `has_more` / `next_cursor`).
  - Request **header** parameters: `offset` (integer, default `0`), `size` (integer, default `20`, maximum `100`).
  - Operation description notes default sort is newest-first by `created.at_time` (implementation detail for T201; document intended behavior).
  - Any authenticated token holder may read (no additional role gate).
  - Responses: `200`/`400` (invalid header values)/`401`/`500`.
- **`POST /api/event`** remains documented; `EventInput` schema reflects the updated MongoDB dictionary (replacing the minimal `context.profile_id`-only stub where the dictionary/test data imply more fields).
- Update the `Event` tag description to reflect create + list semantics.
- OpenAPI path casing matches runtime routes: lowercase `/api/event`.
- The spec parses, every `$ref` resolves, and the API serves it at `/docs/openapi.yaml`.

## Testing Expectations

This is a documentation/contract task; validate the spec rather than runtime list behavior (T201 implements runtime).

Run all commands from the **API repository root**.

- **Spec validation**
  - Parses: `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - No dangling `$ref`s — every `$ref` resolves to a defined component.
  - Confirm `GET /api/event` uses header-based `offset`/`size` and array response body.
  - Confirm `Event` and `EventInput` `context` schemas document identifier fields consistent with configurator output.
- **Lint**
  - `pipenv run lint`
- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - Verify the spec is served: `curl -s http://localhost:8393/docs/openapi.yaml | head`
  - Optionally render in the Swagger explorer (`pipenv run dev` → `/docs`).

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — add `GET /api/event` with offset/size headers and array response; sync `Event` and `EventInput` schemas to MongoDB dictionary

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
