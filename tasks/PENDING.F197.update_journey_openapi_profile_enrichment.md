# F197 – Update OpenAPI for Journey GET profile enrichment

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Contract-first update to `docs/openapi.yaml`: add `Profile` and `JourneyDetail` schemas; document `GET /api/journey` as returning the Journey document with an embedded read-only `profile` loaded from the token owner's Profile id. Mutation responses remain plain `Journey` without `profile`; `JourneyUpdate` must not accept `profile`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — current Journey paths and schemas from `SHIPPED.L110.update_journey_openapi.md`
- `tasks/_PLANNING.md` — task layout, configurator schema discovery, MongoIO rules
- `tasks/SHIPPED.L010.update_resource_openapi.md` — `ResourceDetail` composite pattern
- `tasks/SHIPPED.L110.update_journey_openapi.md` — Journey path and schema baseline

Additional inputs:

- **Definitive Profile schema** from the MongoDB configurator API (start with `pipenv run db` if needed):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Profile.yaml/latest/" -H "accept: application/json"
```

- **Definitive Journey schema** (confirm unchanged persisted shape):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Journey.yaml/latest/" -H "accept: application/json"
```

**External prerequisites**:

- MongoDB configurator serves current `Profile.yaml` and `Journey.yaml` schemas. If the configurator is unavailable, set **Status** to `Blocked` and stop.

**Implementation note**: Runtime enrichment is implemented **locally** in F198/F199 on this branch. Harvest to `api_utils` and bump are **deferred** — see `ISSUE.mentorhub_api_utils.journey_get_profile_enrichment.md`.

## Goals

- **`Profile` component schema** in `docs/openapi.yaml` matches the configurator JSON schema (properties, types, descriptions, optionality, enum values).
- **`Journey` component schema** remains the **persisted** Journey document shape — no `profile` property on the stored document schema.
- New **`JourneyDetail` composite schema**: Journey document fields at the top level plus a required read-only `profile` property referencing `Profile` (same flat shape as runtime `{ ...journeyFields, profile }`, not a nested `{ journey, profile }` wrapper).
- **`GET /api/journey`**:
  - Response `200` body schema → **`JourneyDetail`** (not plain `Journey`).
  - Description: server resolves Journey by token `profile_id` (get-or-create unchanged); embeds the matching Profile document at read time via `MongoIO.get_document` — **not** stored on the Journey collection.
  - Add or extend `404` documentation for **missing Profile** (in addition to existing template-not-found case).
  - No new path or query parameters.
- **Mutation responses stay plain `Journey`** (no `profile` key):
  - `PATCH /api/journey/{journey_id}` → `Journey`
  - `PATCH /api/journey/advance/{resource_id}` → `Journey`
  - `PATCH /api/journey/complete/{resource_id}` → `Journey`
  - `PATCH /api/journey/promote/path/{path_id}` → `Journey`
  - `PATCH /api/journey/promote/module/{path_id}/{module_name}` → `Journey`
- **`JourneyUpdate`**:
  - Must **not** include `profile` in `properties`.
  - Description explicitly lists `profile` among forbidden / non-patchable fields (alongside `_id`, `profile_id`, `created`, `saved`, `library`, `now`, `next`).
- OpenAPI path casing remains lowercase `/api/journey`.
- The spec parses, every `$ref` resolves, and the API serves it at `/docs/openapi.yaml`.
- **Do not** add runtime code, new endpoints, or Profile CRUD paths in this task — OpenAPI only.

## Testing Expectations

This is a documentation/contract task; validate the spec rather than runtime enrichment behavior.

Run all commands from the **API repository root**.

- **Spec validation**
  - Parses: `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - No dangling `$ref`s.
  - Confirm `GET /api/journey` `200` response references **`JourneyDetail`**.
  - Confirm mutation `200` responses reference **`Journey`** only (no `profile`).
  - Confirm **`Profile`** and **`JourneyDetail`** component schemas exist.
  - Confirm **`JourneyUpdate`** does not define `profile`.
- **Lint**
  - `pipenv run lint`
- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - Verify the spec is served: `curl -s http://localhost:8393/docs/openapi.yaml | head`
  - Optionally render in the Swagger explorer (`pipenv run dev` → `/docs`).

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — add `Profile`, `JourneyDetail`; update `GET /api/journey` and `JourneyUpdate` per Goals above

The agent must not update files outside this list.

## Execution Notes
