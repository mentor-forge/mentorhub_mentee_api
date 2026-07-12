# L110 – Update OpenAPI for Journey endpoints

**Status**: Shipped  
**Type**: Feature  
**Depends On**: none  
**Description**: Contract-first update to `docs/openapi.yaml` for the mentee Journey API: sync the `Journey` schema to the MongoDB dictionary, replace the list endpoint with a token-scoped get-or-create read, document ownership RBAC on PATCH, and add `advance` and `complete` mutation paths. Remove `GET /api/journey` infinite-scroll list (no list-journeys page).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — current Journey paths use stale `name`/`description` fields and `/api/Journey` casing
- `tasks/_PLANNING.md` — task layout, configurator schema discovery, MongoIO rules
- `src/routes/journey_routes.py` — runtime blueprint uses lowercase `/api/journey`
- `tasks/SHIPPED.L080.update_path_openapi.md` — pattern for configurator-driven schema sync and lowercase path casing
- `tasks/SHIPPED.L040.cleanup_openapi_aggregation_note_event.md` — pattern for POST/PATCH-only mutation contracts

Additional inputs:

- **Definitive Journey schema** from the MongoDB configurator API (start with `pipenv run db` if needed):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Journey.yaml/latest/" -H "accept: application/json"
```

- **Resource schema** (for `resource_id` path parameters on advance/complete):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Resource.yaml/latest/" -H "accept: application/json"
```

- **Event schema** (for `advanced` and `completed` event types on mutation endpoints):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Event.yaml/latest/" -H "accept: application/json"
```

**External prerequisites**:

- MongoDB configurator serves current `Journey.yaml`, `Resource.yaml`, and `Event.yaml` schemas. The seeded **template Journey** document has `_id` `ffff00000000000000000001` (no `profile_id`; see MongoDB task T117).
- Mentee Journey documents use `_id` equal to the owner's `profile_id` (same value). Legacy test data where Journey `_id` differs from `profile_id` or `resource_id` values are invalid is being corrected in [mentorhub_mongodb_api#45 — F-D19: resource_id test data](https://github.com/mentor-forge/mentorhub_mongodb_api/issues/45). E2E against seeded mentee journeys may remain blocked until that issue ships; OpenAPI and unit tests proceed regardless.
- If the configurator is unavailable, set **Status** to `Blocked` and stop.

## Goals

- **`Journey` component schema** matches the configurator JSON schema:
  - `_id`, `profile_id`, `status`, `library`, `now`, `next`, `later`, `created`, `saved`.
  - Nested item schemas for `library[]`, `now[]`, and `next[]` (modules → topics → resource identifiers).
  - Remove legacy stub fields (`name`, `description`) that are not in the dictionary.
- **Remove list operation**:
  - Delete `GET /api/Journey` (infinite-scroll `getJourneys` operation and its query parameters).
  - Do not document a journeys list endpoint.
- **`GET /api/journey`** (lowercase path):
  - Summary: get the authenticated user's Journey.
  - Description: resolve the Journey using `profile_id` from the JWT (`create_flask_token`). When no document exists, the server clones the template Journey (`ffff00000000000000000001`), sets `_id` and `profile_id` to the token's `profile_id`, and returns the new document (runtime behavior implemented in L120; document the contract here).
  - Response `200` with `Journey` body.
  - Responses: `200` / `400` (missing `profile_id` on token) / `401` / `404` (template missing) / `500`.
  - **Remove** `GET /api/journey/{journey_id}` — the mentee SPA reads only the token owner's journey via `GET /api/journey`.
- **`PATCH /api/journey/{journey_id}`**:
  - Description: update a Journey document. Requires **ownership** (`journey_id` equals token `profile_id`) or **`admin`** in token `roles`; otherwise `403`.
  - Request body: `JourneyUpdate` (fields that remain client-patchable — at minimum `status` and `later`; do not allow patching `library`, `now`, or `next` here; those are server-managed via advance/complete).
  - Responses: `200` / `401` / `403` / `404` / `500`.
- **`PATCH /api/journey/advance/{resource_id}`**:
  - Description: move a resource from `next` to `now` by **Resource ID** (MongoDB ObjectId). Creates an `advanced` Event server-side (runtime in L140).
  - Path parameter `resource_id` (MongoDB ObjectId).
  - No request body required.
  - Response `200` with updated `Journey`.
  - Responses: `200` / `400` / `401` / `403` / `404` (resource unknown or not in `next`) / `500`.
- **`PATCH /api/journey/complete/{resource_id}`**:
  - Description: record completion of a resource in `now` — move it to `library`, update Resource_Aggregation counters (via `AggregationService.add_completion` in L150), and create a `completed` Event server-side.
  - Path parameter `resource_id` (MongoDB ObjectId).
  - Optional request body: `JourneyCompleteInput` with optional `rating` (1–4), `note`, and `duration` (ISO 8601 duration) for aggregation/note side effects.
  - Response `200` with updated `Journey`.
  - Responses: `200` / `400` / `401` / `403` / `404` / `500`.
- Add component schemas: `JourneyLibraryItem`, `JourneyNowItem`, `JourneyNextModule`, `JourneyNextTopic`, `JourneyCompleteInput`, and an updated `JourneyUpdate` aligned to the dictionary.
- OpenAPI path casing matches runtime routes: lowercase `/api/journey`, not `/api/Journey`.
- Update the `Journey` tag description to reflect token-scoped read, ownership RBAC, and advance/complete mutations.
- The spec parses, every `$ref` resolves, and the API serves it at `/docs/openapi.yaml`.
- **Do not** add runtime code in this task — OpenAPI only.

## Testing Expectations

This is a documentation/contract task; validate the spec rather than runtime behavior.

Run all commands from the **API repository root**.

- **Spec validation**
  - Parses: `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - No dangling `$ref`s.
  - Confirm **no** `GET` list/infinite-scroll Journey operation remains.
  - Confirm `GET /api/journey` is documented (no `{journey_id}` GET).
  - Confirm `PATCH /api/journey/advance/{resource_id}` and `PATCH /api/journey/complete/{resource_id}` are documented.
  - Confirm `Journey` schema includes `library`, `now`, `next`, `later`, `profile_id` (not legacy `name`/`description` stubs).
- **Lint**
  - `pipenv run lint`
- **Packaging verification**
  - `pipenv run container` — build API container image
  - `pipenv run api` — run db + API containers
  - Verify the spec is served: `curl -s http://localhost:8393/docs/openapi.yaml | head`
  - Optionally render in the Swagger explorer (`pipenv run dev` → `/docs`).

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — sync Journey schemas and paths per Goals above

The agent must not update files outside this list.

## Execution Notes

**Summary**
- Synced Journey OpenAPI to MongoDB dictionary (`library`, `now`, `next`, `later`, `profile_id`).
- Replaced list/GET-by-id with token-scoped `GET /api/journey`.
- Documented `PATCH` ownership RBAC, `advance/{resource_id}`, and `complete/{resource_id}`.
- Fixed path casing to lowercase `/api/journey`.

**Testing**
- OpenAPI YAML parse validated.
- `pipenv run lint` passed.
- `pipenv run container` succeeded.
