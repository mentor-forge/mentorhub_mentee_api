# L100 – Enrich Path detail with Resource name and description

**Status**: Pending  
**Type**: Feature  
**Depends On**: L080  
**Description**: Extend `GET /api/path/{path_id}` so nested `modules[].topics[].resources[]` entries include minimal Resource data (`_id`, `name`, `description`). Add `ResourceService.get_resources_by_ids` for batch lookup; `PathService.get_path` collects resource IDs from the Path document, fetches Resources, and merges summaries into each topic's `resources` array.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — Path detail contract and `PathResourceSummary` from L080

Additional inputs:

- `src/services/path_service.py` — `get_path` currently returns raw MongoDB document via `mongo.get_document`
- `src/services/resource_service.py` — `get_resources` (paginated list) and `get_resource` (single detail composite); add batch-by-ids helper here
- `../mentorhub_mongodb_api/configurator/dictionaries/Path.0.1.0.yaml` — `modules[].topics[].resources[]` stores Resource `_id` identifiers
- `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py` — `get_documents` with `match={"_id": {"$in": [...]}}` and optional `project`
- `test/routes/test_path_routes.py`
- `test/services/test_path_service.py`
- `test/services/test_resource_service.py` — **new or updated** tests for batch lookup
- `test/e2e/test_path.py`

**MongoDB I/O rule**: Batch Resource reads must use `MongoIO.get_documents` (e.g. `match={"_id": {"$in": object_ids}}`, `project={"name": 1, "description": 1}`) — not direct `collection.find`.

**Archived resources**: When enriching Path detail, apply the same visibility rule as `ResourceService.get_resources` — non-admin callers should not receive `archived` resources (omit or redact entries for archived IDs; document chosen behavior in Execution Notes). Admin callers may see archived resource summaries.

## Goals

- `ResourceService.get_resources_by_ids(resource_ids, token, breadcrumb)` (name may vary slightly but must be clearly distinct from paginated `get_resources`):
  - Accepts a list of Resource ID strings (deduplicated).
  - Returns a list of minimal resource dicts with at least `_id`, `name`, and `description` (projection or post-processing).
  - Uses `MongoIO.get_documents` with `_id: {$in: ...}` match.
  - Honors archived visibility for non-admin callers (consistent with `ResourceService.get_resources`).
  - Returns an empty list when `resource_ids` is empty; does not raise for unknown IDs (missing IDs are simply omitted from results).
- `PathService.get_path(path_id, token, breadcrumb)`:
  - Loads the Path document via `mongo.get_document` (unchanged lookup).
  - Walks `modules` → `topics` → `resources` to collect all Resource IDs.
  - Calls `ResourceService.get_resources_by_ids` once with the collected IDs.
  - Replaces each topic's `resources` array: where a summary exists for an ID, emit `{_id, name, description}`; preserve array order from the Path document; omit or skip IDs with no accessible Resource (document behavior for missing/archived IDs).
  - Returns the Path document with enriched nested resources (other Path fields unchanged).
- Route handler `GET /api/path/<path_id>` continues to return the enriched Path JSON (`200`) — no route signature change beyond response shape.
- Unit tests cover batch Resource lookup, enrichment logic, empty/missing IDs, and archived filtering.
- E2E test asserts `GET /api/path/{path_id}` returns enriched `resources` entries with `name` and `description` when test data includes modules/topics/resources.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_resource_service.py` — batch lookup by IDs; projection shape; archived filter for non-admin.
  - `test/services/test_path_service.py` — `get_path` enriches nested resources; handles paths with no modules; handles missing resource IDs.
  - `test/routes/test_path_routes.py` — detail route returns enriched path shape (mock service).
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e`
  - `test/e2e/test_path.py` — add or extend test: fetch a path by ID and assert `modules[].topics[].resources[]` items include `name` and `description` when present in seed data.
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API

## Outputs

Paths are relative to the **API repository root**.

- `src/services/resource_service.py` — add `get_resources_by_ids` batch lookup with minimal projection and archived visibility
- `src/services/path_service.py` — enrich `get_path` nested `resources` via `ResourceService.get_resources_by_ids`
- `test/services/test_resource_service.py` — tests for batch lookup
- `test/services/test_path_service.py` — tests for resource enrichment in `get_path`
- `test/routes/test_path_routes.py` — updated detail route tests if response shape assertions change
- `test/e2e/test_path.py` — E2E assertions for enriched path detail

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
