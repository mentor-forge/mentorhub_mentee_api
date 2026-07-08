# L010 – Update OpenAPI for Resource schema and endpoints

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Fetch the latest `Resource` JSON schema from the MongoDB configurator and update `docs/openapi.yaml` to match. Contract-first: simplify `GET /api/resource` to return a plain array with `offset`/`size` request headers; define `ResourceDetail` for `GET /api/resource/{id}` (resource + aggregation + notes); remove any `PATCH` on Resource (mentees cannot update resources).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml`

Additional inputs:

- Latest schema from the MongoDB configurator (configurator API on port `8383`; start with `pipenv run db` if needed):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Resource.yaml/latest/" -H "accept: application/json"

curl -X GET "http://localhost:8383/api/configurations/json_schema/Resource_Aggregation.yaml/latest/" -H "accept: application/json"

curl -X GET "http://localhost:8383/api/configurations/json_schema/Note.yaml/latest/" -H "accept: application/json"
```

- `src/routes/resource_routes.py` — actual blueprint paths use lowercase `/api/resource` (align OpenAPI paths with runtime routes)
- `src/services/resource_service.py` — current read-only behavior

**External prerequisite**: MongoDB `Resource` dictionary has already been updated to include the `archived` `resource_status` value, and the configurator serves that latest schema at the URLs above. Do not orchestrate this task until that database/configurator change is actually available in the running environment. If the configurator is unavailable, try `pipenv run db`; if the API call still fails, set **Status** to `Blocked` and stop.

## Goals

- `Resource` component schema in `docs/openapi.yaml` matches the latest configurator JSON schema (properties, types, descriptions, optionality, enum values) — including fields absent from the current stub spec such as `url`, `type`, `cost`, `skill_level`, `interests`, `technologies`, `last_verified`, `created`, and `saved`, and including `archived` in the `status` enum.
- New `ResourceAggregation` component schema matches `Resource_Aggregation.0.1.0.yaml` (`resource_id`, `note_count`, `completions`, `hits`, `duration`, `rating_count`, `rating_sum`, `created`, `last_saved`).
- New `ResourceDetail` composite schema: `{ resource: Resource, aggregation: ResourceAggregation | null, notes: [Note, ...] }`.
- `GET /api/resource` documented as:
  - Returns `200` with a **JSON array** of `Resource` objects (not an infinite-scroll wrapper).
  - Request **header** parameters: `offset` (integer, default `0`), `size` (integer, default `20`, set a reasonable maximum such as `100`).
  - Documents that non-`admin` callers receive only resources whose `status` is not `archived`.
  - `admin` role may see all resources including `archived`.
  - Responses: `200`/`401`/`500` (no `400` unless invalid header values are validated).
- `GET /api/resource/{resource_id}` documented to return `ResourceDetail` (read-only); responses `200`/`401`/`404`/`500`.
- **No** `PATCH /api/resource/{resource_id}` operation (remove if present; mentees cannot update resources).
- OpenAPI path casing matches runtime routes: `/api/resource` and `/api/resource/{resource_id}` (lowercase), not `/api/Resource`.
- The spec parses, every `$ref` resolves, and the API serves it at `/docs/openapi.yaml`.

## Testing Expectations

This is a documentation/contract task; validate the spec rather than runtime behavior.

Run all commands from the **API repository root**.

- **Spec validation**
  - Parses: `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - No dangling `$ref`s — every `$ref` resolves to a defined component.
- **Lint**
  - `pipenv run lint`
- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - Verify the spec is served: `curl -s http://localhost:8393/docs/openapi.yaml | head`
  - Optionally render in the Swagger explorer (`pipenv run dev` → `/docs`).

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — update `Resource` schema; add `ResourceAggregation` and `ResourceDetail`; update `GET /api/resource` list contract (array + header pagination + archived filter documentation); update `GET /api/resource/{resource_id}` to `ResourceDetail`; remove any Resource `PATCH` operation; fix path casing to lowercase `/api/resource`.

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
