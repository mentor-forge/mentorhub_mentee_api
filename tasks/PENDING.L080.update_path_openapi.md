# L080 – Update OpenAPI for Path list and detail endpoints

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Contract-first update to `docs/openapi.yaml` for Path endpoints: `GET /api/path` returns a plain JSON array of all paths sorted by name (no pagination or infinite scroll); `GET /api/path/{path_id}` returns a Path with nested `modules[].topics[].resources[]` entries enriched with minimal Resource fields (`_id`, `name`, `description`). Align OpenAPI path casing with runtime routes (`/api/path`, lowercase).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml`

Additional inputs:

- Latest Path dictionary schema from the MongoDB configurator (start with `pipenv run db` if needed):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Path.yaml/latest/" -H "accept: application/json"
```

- Generated JSON schema: `../mentorhub/Specifications/schemas/Path.schema.json` (if present)
- Path dictionary source: `../mentorhub_mongodb_api/configurator/dictionaries/Path.0.1.0.yaml` — nested `modules` → `topics` → `resources` (array of Resource `_id` identifiers)
- `src/routes/path_routes.py` — runtime blueprint uses lowercase `/api/path`
- `tasks/SHIPPED.L010.update_resource_openapi.md` — pattern for list/detail contract changes and lowercase path casing
- `tasks/SHIPPED.L020.simplify_resource_list_pagination.md` — pattern for replacing infinite-scroll wrapper with a plain array

**MongoDB I/O rule** (for downstream implementation tasks): services must use `MongoIO` (`get_document`, `get_documents`, etc.) — not direct PyMongo collection calls.

## Goals

- `Path` component schema in `docs/openapi.yaml` reflects the MongoDB Path dictionary, including at minimum: `_id`, `name`, `description`, `technologies`, `interests`, `modules` (with nested `topics` and `resources`), `status`, `created`, `saved`.
- New `PathResourceSummary` component schema (or equivalent name) with required `_id` and optional `name`, `description` — minimal Resource projection for Path detail responses.
- In the Path detail response, each item in `modules[].topics[].resources[]` is documented as `PathResourceSummary` (identifier plus `name` and `description`), not a bare ObjectId string.
- `GET /api/path` documented as:
  - Returns `200` with a **JSON array** of `Path` objects (not an infinite-scroll wrapper).
  - Results are sorted by `name` ascending (server-side; not client-selectable).
  - **No** pagination or infinite-scroll query parameters (`after_id`, `limit`, `sort_by`, `order`).
  - **No** optional `name` query filter unless product requires it — default contract is return all paths.
  - Responses: `200` / `401` / `500`.
- `GET /api/path/{path_id}` documented to return a full `Path` document with enriched `modules[].topics[].resources[]` as `PathResourceSummary` objects; responses `200` / `401` / `404` / `500`.
- OpenAPI path casing matches runtime routes: `/api/path` and `/api/path/{path_id}` (lowercase), not `/api/Path` / `/api/Path/{PathId}`.
- Remove or stop referencing Path-specific infinite-scroll response shapes on these operations (the shared `InfiniteScrollResponse` component may remain for other domains).
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

- `docs/openapi.yaml` — sync `Path` schema with MongoDB dictionary; add `PathResourceSummary`; update `GET /api/path` (plain array, name-sorted, no pagination/scroll params); update `GET /api/path/{path_id}` (enriched resources in nested modules); fix path casing to lowercase `/api/path`.

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
