# F203 – OpenAPI for 1.0.0 consume GETs

**Status:** Shipped  
**Type:** Feature  
**Depends On:** none  
**Description:** First task of the F-EA12 / F-EA13 1.0.0 wave (same PR). Document the consume GETs that shared `create_*_get_routes` factories will mount, without changing existing Journey control, Note POST, Event POST, Aggregation composite, Resource composite, or Path enrich contracts. No Python in this task. The `api-utils==1.0.0` pin is F208 so current 0.5.2 routes stay green until subclasses exist.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — bounded domains; OpenAPI is the SPA contract; Mentee **controls** Journey, Rating, and Note; **creates** Event; **consumes** Resource and Path
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — OpenAPI is grounded in the database validation schema
- `tasks/_PLANNING.md` — fetch schemas from the running configurator only when component schemas change
- `README.md`
- `../mentorhub_api_utils/README.md` — list GET is a JSON **array**; pagination is request headers `offset` (default `0`) and `size` (default `20`, max `100`); query `contains` / `in_list` plus `sort_by` / `order`; no cursor envelope; no pagination response headers
- `../mentorhub_api_utils/api_utils/routes/shared_get_routes.py` — factory URL shapes: journey by-id only; note list requires `resource_id`; event list only; resource list + by-id; path list + by-id; aggregation by-id is a **plain** document (this API keeps the composite instead)
- `../mentorhub_api_utils/api_utils/services/note_service.py` — `NOTE_LIST_FILTERS` / `NOTE_LIST_ORDER`
- `../mentorhub_api_utils/api_utils/services/event_service.py` — `EVENT_LIST_FILTERS` / `EVENT_LIST_ORDER`
- `docs/openapi.yaml` — current spec: `GET /api/journey` is get-or-create + embedded profile (`JourneyDetail`); `PATCH /api/journey/{journey_id}` only (no GET); Note and Event are POST-only; Aggregation GET returns `AggregationDetail`; Resource/Path by-id already document enrich/composite
- `../mentorhub/Specifications/architecture.yaml` — Mentee controls Journey / Rating / Note; creates Event; consumes Resource / Path

**Do not change these existing operations** (HTTP contract is unchanged for F-EA12 control routes and current BFF composites):

| Method and path | Keep |
| --- | --- |
| `GET /api/journey` | `JourneyDetail` (Journey + embedded `profile`); get-or-create |
| `PATCH /api/journey/promote/path/{path_id}` | plain `Journey` |
| `PATCH /api/journey/promote/module/{path_id}/{module_name}` | plain `Journey` |
| `PATCH /api/journey/advance/{resource_id}` | plain `Journey` |
| `PATCH /api/journey/complete/{resource_id}` | plain `Journey` |
| `PATCH /api/journey/{journey_id}` | plain `Journey` |
| `POST /api/note` | created `Note` |
| `POST /api/event` | created `Event` |
| `GET /api/aggregation/{resource_id}` | `AggregationDetail` `{aggregation, notes}` — **not** a plain aggregation document |
| `GET /api/resource` / `GET /api/resource/{resource_id}` | array / `ResourceDetail` composite |
| `GET /api/path` / `GET /api/path/{path_id}` | array / `PathDetail` with resource enrich |

**Add these operations** (factories in F208):

| Method and path | Body out | Notes |
| --- | --- | --- |
| `GET /api/journey/{journey_id}` | `Journey` | consume by-id; 404 when missing or hidden by outbound RBAC; **not** `JourneyDetail` |
| `GET /api/note` | `Note[]` | required query `resource_id`; `offset`/`size` headers |
| `GET /api/event` | `Event[]` | `offset`/`size` headers; optional `profile_id` query as the event factory supports |

Reuse existing component schemas (`Journey`, `Note`, `Event`, `JourneyDetail`, …). Do **not** add Rating, Profile, or Customer paths. Do **not** add Resource or Path POST (Mentor **controls** Resource).

If a component schema is missing a field the live dictionary has, fetch from the running configurator (`pipenv run db` first):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Journey.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Note.yaml/latest/" -H "accept: application/json"
curl -X GET "http://localhost:8383/api/configurations/json_schema/Event.yaml/latest/" -H "accept: application/json"
```

If this task only adds paths that reuse **existing** components, do not Block on the configurator.

## Goals

- `docs/openapi.yaml` documents `GET /api/journey/{journey_id}` (plain `Journey`, path param `^[0-9a-fA-F]{24}$`, `404` when missing/hidden). Same path keeps the existing PATCH.
- `GET /api/note` list: bearer auth; required `resource_id` query; `offset`/`size` request headers (defaults `0` / `20`, max `100`); `200` body is a JSON **array** of `Note`; document `contains` / `in_list` filters and `sort_by` / `order` from `NOTE_LIST_FILTERS` / `NOTE_LIST_ORDER`. Existing POST on `/api/note` stays.
- `GET /api/event` list: same pagination headers; `200` body is a JSON **array** of `Event`; document filters from `EVENT_LIST_FILTERS` / `EVENT_LIST_ORDER`; optional `profile_id` query. Existing POST stays.
- Tags: Note and Event descriptions are list+create, not “create only”. Journey tag mentions consume GET by-id plus local get-or-create.
- No `after_id`, `has_more`, `next_cursor`, or `X-Pagination-*`.
- Aggregation by-id remains `AggregationDetail`. Do not document a plain-document aggregation GET.
- The document remains valid OpenAPI 3.0.x.
- No Python, Pipfile, or README changes.

## Testing Expectations

Run all commands from this API repository root.

- **Spec validation**
  - `python3 -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - Confirm the three new GET operations, array list responses, `offset`/`size` headers, unchanged control/composite operations, and no cursor envelope.
- **Unit / lint / build** (docs-only; suite must still pass on `api-utils==0.5.2`)
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8393/docs/openapi.yaml` — served file includes the new GETs and keeps existing Journey PATCH / Aggregation composite paths

## Outputs

- `docs/openapi.yaml` — add journey by-id GET, note list GET, event list GET; keep existing control and composite operations

The agent must not update files outside this list.

## Execution Notes

- Updated `docs/openapi.yaml`:
  - Documented `GET /api/journey/{journey_id}` (plain Journey, 404 on missing/hidden).
  - Documented `GET /api/note` list with required `resource_id` query, `offset`/`size` headers, `status` filter, `created.at_time` sort.
  - Documented `GET /api/event` list with `offset`/`size` headers, `type` filter, optional `profile_id` query, `created.at_time` / `type` sort.
  - Updated Journey, Note, and Event tag descriptions.
  - Removed obsolete `InfiniteScrollResponse` component schema.
- Validated YAML syntax with `python3 -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`.
- Executed `pipenv run test`, `pipenv run lint`, and `pipenv run build` successfully.
