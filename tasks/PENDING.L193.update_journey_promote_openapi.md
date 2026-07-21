# L193 – Update OpenAPI for Journey promote mutations (later → next)

**Status**: Pending  
**Type**: Feature  
**Depends On**: none  
**Description**: Contract-first update to `docs/openapi.yaml` for two Journey mutations that copy Path content from `later` into `next`: **Promote Path to Next** (all modules) and **Promote Module to Next** (single module).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — existing Journey paths (`GET /api/journey`, `PATCH .../advance`, `PATCH .../complete`, `PATCH /api/journey/{journey_id}`)
- `tasks/_PLANNING.md` — task layout, configurator schema discovery
- `tasks/SHIPPED.L110.update_journey_openapi.md` — Journey OpenAPI patterns
- `tasks/ISSUE.mentorhub_api_utils.journey_promote_mutations.md` — runtime behavior summary

Additional inputs:

- **Definitive Journey schema** from the MongoDB configurator API (start with `pipenv run db` if needed):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Journey.yaml/latest/" -H "accept: application/json"
```

- **Path schema** (module/topic shape copied into `next[]`):

```bash
curl -X GET "http://localhost:8383/api/configurations/json_schema/Path.yaml/latest/" -H "accept: application/json"
```

**External prerequisites**:

- MongoDB configurator serves current `Journey.yaml` and `Path.yaml` schemas.
- If the configurator is unavailable, set **Status** to `Blocked` and stop.

## Goals

- **`PATCH /api/journey/promote/path/{path_id}`**:
  - Summary: Promote Path to Next — copy all Path modules into Journey `next`.
  - Description: Load the Path by id. When the Path id is present in the caller's Journey `later[]`, deep-copy every module (name, description, topics, resource ids) onto `next[]` and remove the Path id from `later[]`. Requires authenticated mentee (`profile_id` on token). Server-managed; not patchable via `JourneyUpdate`.
  - `operationId`: `promoteJourneyPath`
  - Path parameter `path_id` (MongoDB ObjectId).
  - No request body.
  - Response `200` with updated `Journey`.
  - Responses: `200` / `400` / `401` / `403` / `404` (Path unknown or not in `later`) / `500`.
- **`PATCH /api/journey/promote/module/{path_id}/{module_name}`**:
  - Summary: Promote Module to Next — copy one Path module into Journey `next`.
  - Description: Load the Path by id and locate the module by exact `module_name`. When the Path id is in `later[]`, append that module to `next[]` without removing the Path from `later`. Reject when a module with the same name already exists in `next` (`400`).
  - `operationId`: `promoteJourneyModule`
  - Path parameters: `path_id` (ObjectId), `module_name` (Path module `name` / word pattern).
  - No request body.
  - Response `200` with updated `Journey`.
  - Responses: `200` / `400` (duplicate module in `next`, invalid params) / `401` / `403` / `404` (Path, module, or later membership) / `500`.
- Update the **Journey** tag description to mention promote mutations alongside advance/complete.
- OpenAPI path casing remains lowercase `/api/journey/...`.
- Register promote paths **before** `PATCH /api/journey/{journey_id}` in the spec ordering notes (runtime route order is implemented in L195/L196).
- The spec parses, every `$ref` resolves, and the API serves it at `/docs/openapi.yaml`.
- **Do not** add runtime code in this task — OpenAPI only.

## Testing Expectations

This is a documentation/contract task; validate the spec rather than runtime behavior.

Run all commands from the **API repository root**.

- **Spec validation**
  - Parses: `pipenv run python -c "import yaml; yaml.safe_load(open('docs/openapi.yaml'))"`
  - No dangling `$ref`s.
  - Confirm both promote paths are documented with correct path parameters and `200` → `Journey` responses.
  - Confirm existing advance/complete/GET/PATCH contracts are unchanged.
- **Lint**
  - `pipenv run lint`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - Verify the spec is served: `curl -s http://localhost:8393/docs/openapi.yaml | head`

## Outputs

Paths are relative to the **API repository root**.

- `docs/openapi.yaml` — add promote path and promote module operations per Goals

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
