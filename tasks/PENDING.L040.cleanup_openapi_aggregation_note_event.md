# L040 – Clean up OpenAPI for Aggregation, Note, and Event

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Update `docs/openapi.yaml` to remove obsolete Rating operations, restrict Note and Event paths to POST-only, and document the new `GET /api/aggregation/{resource_id}` composite endpoint.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — current spec (includes stale Rating paths and Note/Event GET operations)
- `src/server.py` - runtime entrypoint, route registration
- `src/routes/note_routes.py` — runtime already exposes POST-only `/api/note`
- `src/routes/event_routes.py` — runtime still exposes GET; spec should document POST-only target contract
- `tasks/SHIPPED.L010.update_resource_openapi.md` — `ResourceAggregation` schema and lowercase path conventions
- `tasks/SHIPPED.L030.resource_detail_aggregation_and_notes.md` — prior aggregation/notes composite patterns

Configurator schema URLs (start `pipenv run db` if needed):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Note.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Event.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Resource_Aggregation.yaml/latest/" -H "accept: application/json"
```

## Goals

- **Remove Rating entirely** from the OpenAPI document:
  - Delete the `Rating` tag.
  - Delete `/api/Rating` and `/api/Rating/{RatingId}` path items.
  - Delete `Rating`, `RatingInput`, and `RatingUpdate` component schemas.
  - Remove any dangling `$ref`s to Rating schemas.
- **Note — POST only**:
  - Document a single operation: `POST /api/note` (lowercase path, matching runtime).
  - Remove `GET /api/Note`, `GET /api/Note/{NoteId}`, and `PATCH /api/Note/{NoteId}` operations.
  - Sync `Note` and `NoteInput` component schemas with the MongoDB dictionary (`resource_id`, `profile_id`, `note`, `status`, `created`, `saved` — not legacy `name`/`description` stubs).
  - Remove `NoteUpdate` schema (no PATCH operation).
  - Update tag description to reflect create-only semantics.
- **Event — POST only**:
  - Document a single operation: `POST /api/event` (lowercase path).
  - Remove `GET /api/Event`, `GET /api/Event/{EventId}` operations.
  - Sync `Event` and `EventInput` component schemas with the MongoDB dictionary (`type`, `context`, `created` — not legacy `name`/`description` stubs).
  - Update tag description to reflect create-only semantics.
- **Aggregation — new read endpoint**:
  - Add an `Aggregation` tag.
  - Document `GET /api/aggregation/{resource_id}`:
    - Returns `200` with an `AggregationDetail` composite: `{ aggregation: ResourceAggregation, notes: [Note, ...] }`.
    - When no aggregation document exists for the resource, the API creates one (document this behavior in the operation description).
    - Any authenticated token holder may read (no additional role gate beyond valid JWT).
    - Responses: `200`/`400` (invalid ObjectId)/`401`/`500`.
  - Add `AggregationDetail` component schema reusing existing `ResourceAggregation` and `Note` schemas.
  - Confirm `ResourceAggregation` matches `Resource_Aggregation.1.0.0.yaml` field set.
- OpenAPI path casing matches runtime routes (lowercase `/api/note`, `/api/event`, `/api/aggregation`).
- The spec parses, every `$ref` resolves, and the API serves it at `/docs/openapi.yaml`.

## Testing Expectations

This is a documentation/contract task; validate the spec rather than runtime behavior.

Run all commands from the **API repository root**.

- **Spec validation**
  - Parses: `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - No dangling `$ref`s — every `$ref` resolves to a defined component.
  - Confirm Rating paths and schemas are fully removed.
  - Confirm Note and Event paths expose POST only.
  - Confirm `GET /api/aggregation/{resource_id}` and `AggregationDetail` are present.
- **Lint**
  - `pipenv run lint`
- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - Verify the spec is served: `curl -s http://localhost:8393/docs/openapi.yaml | head`
  - Optionally render in the Swagger explorer (`pipenv run dev` → `/docs`).

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — remove Rating; Note and Event POST-only; add Aggregation GET and `AggregationDetail`; sync Note/Event schemas to MongoDB dictionaries; fix path casing.

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
