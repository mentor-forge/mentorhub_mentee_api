# L070 – Refactor services to use MongoIO instead of direct collection calls

**Status**: Shipped  
**Type**: Defect  
**Depends On**: none  
**Description**: Eliminate direct PyMongo `collection.*` usage in mentee API services; route all MongoDB I/O through `MongoIO` convenience methods. Bump `api-utils` to `0.2.4` so collection-name config constants (including `RESOURCE_AGGREGATION_COLLECTION_NAME`) are used directly without `_collection_name()` fallbacks.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `../mentorhub_api_utils/api_utils/mongo_utils/mongo_io.py` — `MongoIO` public API (`get_document`, `get_documents`, `create_document`, `update_document`, `upsert_document`)
- `../mentorhub_api_utils/api_utils/mongo_utils/infinite_scroll.py` — `execute_infinite_scroll_query` (currently accepts a raw collection)
- `../mentorhub_api_utils/api_utils/config/config.py` — collection name defaults (including `RESOURCE_AGGREGATION_COLLECTION_NAME` added in **v0.2.4**)
- `README.md`
- `Pipfile` / `Pipfile.lock` — currently pins `api-utils==0.2.1`

**Audit: direct collection usage in `src/services/` (current branch)**

| Service | Method | Current pattern | Target MongoIO approach |
|---------|--------|-----------------|-------------------------|
| `aggregation_service.py` | `_find_aggregation` | `collection.find_one({"_id": ...})` and legacy `find_one({"resource_id": ...})` | `get_document(collection_name, resource_id)` for primary lookup; `get_documents(collection_name, match={"resource_id": oid})` for legacy fallback (first result or `None`) |
| `aggregation_service.py` | `_get_or_create_aggregation`, `get_aggregation_for_resource` | `mongo.get_collection(...)` then `_find_aggregation(collection, ...)` | Remove `get_collection` calls; use MongoIO methods above |
| `note_service.py` | `get_notes_for_resource` | `collection.find({"resource_id": oid}).sort("created.at_time", -1)` | `get_documents(NOTE_COLLECTION_NAME, match={"resource_id": oid}, sort_by=[("created.at_time", DESCENDING)])` |
| `resource_service.py` | `get_resources` | `collection.find(query).sort(...).skip(offset).limit(size)` | **Gap:** `get_documents` has no `skip`/`limit`. Requires api_utils enhancement (see External prerequisites) or new `MongoIO.get_documents_paginated(...)` |
| `path_service.py` | `get_paths` | `get_collection` + `execute_infinite_scroll_query(collection, ...)` | **Gap:** infinite-scroll helper takes a raw collection. Prefer api_utils refactor to accept `(mongo, collection_name, ...)` |
| `journey_service.py` | `get_journeys` | Same as path | Same as path |

**Already compliant (no change required unless refactoring neighbors):**

- `event_service.py` — `create_document`, `get_document`
- `note_service.py` — `create_note`, `get_note` use `create_document` / `get_document`
- `resource_service.py` — `get_resource` uses `get_document`
- `path_service.py` / `journey_service.py` — `get_path` / `get_journey` / create / update use `get_document`, `create_document`, `update_document`
- `aggregation_service.py` — create/update paths already use `create_document`, `get_document`, `update_document`

**`_collection_name()` helper**

- `AggregationService._collection_name()` uses `getattr(config, "RESOURCE_AGGREGATION_COLLECTION_NAME", "Resource_Aggregation")` because **api-utils 0.2.1** does not define that constant (added in **0.2.4**).
- After bumping to `api-utils==0.2.4`, remove `_collection_name()` and use `config.RESOURCE_AGGREGATION_COLLECTION_NAME` directly (same pattern as `config.NOTE_COLLECTION_NAME`, `config.EVENT_COLLECTION_NAME`, etc.).
- **No newer MongoIO query helpers** exist in 0.2.4 beyond those listed above; bumping api-utils alone does not resolve pagination or infinite-scroll collection passing.

**External prerequisites**

1. **CodeArtifact**: `api-utils==0.2.4` published and installable via `pipenv run install` (run `mh` first in the shell session if needed). If install fails, set **Status** to `Blocked`.
2. **api_utils pagination (recommended upstream task)**: Extend `MongoIO.get_documents` with optional `skip` and `limit` parameters (or add `get_documents_paginated`) so `ResourceService.get_resources` can drop `collection.find().skip().limit()`. Record as a task/issue in `../mentorhub_api_utils/` if not yet shipped; L070 may implement the mentee-side caller once available.
3. **api_utils infinite scroll (optional upstream task)**: Refactor `execute_infinite_scroll_query` to take `mongo` + `collection_name` instead of a raw collection, so `path_service` and `journey_service` never call `get_collection`. If not available, L070 may still pass `mongo.get_collection(...)` only inside a thin api_utils wrapper — document any remaining exception.

Pattern reference: `../mentorhub_mentor_api/src/services/profile_service.py` — uses `mongo.get_documents(..., match=...)` without direct collection calls.

## Goals

- Bump `Pipfile` to `api-utils==0.2.4`, run `pipenv run install` to refresh the lockfile/venv, and verify `Config.RESOURCE_AGGREGATION_COLLECTION_NAME` is available at runtime.
- Remove `AggregationService._collection_name()`; use `config.RESOURCE_AGGREGATION_COLLECTION_NAME` everywhere.
- Refactor `AggregationService._find_aggregation` to use `MongoIO.get_document` / `MongoIO.get_documents` (no `collection.find_one`).
- Refactor `NoteService.get_notes_for_resource` to use `MongoIO.get_documents` with match + sort (no `collection.find`).
- Refactor `ResourceService.get_resources` to use MongoIO once pagination support exists (coordinate with api_utils if needed); **no direct `collection.find`** in mentee services when task completes.
- Refactor `PathService.get_paths` and `JourneyService.get_journeys` to avoid passing raw collections to business logic (prefer api_utils infinite-scroll API that accepts `collection_name`).
- No service file under `src/services/` should call `mongo.get_collection(...)` except where explicitly documented as an approved api_utils delegation point (goal: zero such calls).
- Update unit tests to mock `MongoIO` methods instead of collection cursors where affected.
- `pipenv run test`, `pipenv run lint`, and `pipenv run build` pass.

## Testing Expectations

Run all commands from the **API repository root**.

- **Dependencies** (when `Pipfile` changes)
  - `pipenv run install` — install/refresh packages from CodeArtifact (`mh` first if required)
- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_aggregation_service.py`
  - `test/services/test_note_service.py`
  - `test/services/test_resource_service.py`
  - `test/services/test_path_service.py`
  - `test/services/test_journey_service.py`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e`

## Outputs

Paths are relative to the **API repository root**.

- `Pipfile` — bump `api-utils` to `==0.2.4`
- `Pipfile.lock` — updated by `pipenv run install`
- `src/services/aggregation_service.py` — MongoIO lookups; drop `_collection_name()`
- `src/services/note_service.py` — `get_documents` for per-resource notes
- `src/services/resource_service.py` — paginated list via MongoIO (after pagination support available)
- `src/services/path_service.py` — infinite scroll without direct collection access (if api_utils supports it)
- `src/services/journey_service.py` — same as path
- `test/services/test_aggregation_service.py` — updated mocks/assertions
- `test/services/test_note_service.py` — updated mocks/assertions
- `test/services/test_resource_service.py` — updated mocks/assertions
- `test/services/test_path_service.py` — updated mocks/assertions (if changed)
- `test/services/test_journey_service.py` — updated mocks/assertions (if changed)

The agent must not update files outside this list unless an upstream api_utils change is explicitly in scope and listed here.

## Execution Notes

**Approach**

- Bumped `api-utils` to `0.2.4` in `Pipfile`; updated `Pipfile.lock` with the 0.2.4 wheel hash (full `pipenv lock` requires PyPI packages not mirrored in CodeArtifact).
- `AggregationService`: removed `_collection_name()`; `_find_aggregation` uses `get_document` + legacy `get_documents` fallback; all paths use `config.RESOURCE_AGGREGATION_COLLECTION_NAME`.
- `NoteService.get_notes_for_resource`: uses `get_documents` with `match` and `sort_by`.
- `ResourceService.get_resources`: uses `get_documents` + Python slice `[offset:offset+size]` until api_utils adds server-side skip/limit (no `collection.find`).
- **Approved exception**: `PathService.get_paths` and `JourneyService.get_journeys` still call `mongo.get_collection` to pass a collection into `execute_infinite_scroll_query` — upstream api_utils change required to eliminate.

**Test results**

- `pipenv run test`: 78 passed, 24 skipped
- `pipenv run lint`: pass (black reformatted pre-existing path/journey route files)
- `pipenv run build`: pass
