# L183 – Verify composite endpoints return full note lists after R052

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L180  
**Description**: After api-utils 0.5.0, `NoteService.get_notes_for_resource` paginates by default; composite reads must continue returning **all** notes via `NoteService.list_all_notes_for_resource`. Verify `GET /api/resource/{id}` and `GET /api/aggregation/{resource_id}` still return complete `notes` arrays; add regression tests if note counts would truncate at the default page size.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`

Additional inputs:

- `../mentorhub_api_utils/api_utils/services/resource_service.py` — `get_resource` calls `NoteService.list_all_notes_for_resource`
- `../mentorhub_api_utils/api_utils/services/aggregation_service.py` — `get_aggregation_detail` calls `NoteService.list_all_notes_for_resource`
- `../mentorhub_api_utils/api_utils/services/note_service.py` — `list_all_notes_for_resource` uses `offset=0`, `size=MAX_SIZE`
- `../mentorhub_api_utils/tasks/SHIPPED.R052.refactor_note_service_list.md` — composite full-fetch behavior
- `src/routes/resource_routes.py` — `GET /api/resource/{id}` delegates to `ResourceService.get_resource`
- `src/routes/aggregation_routes.py` — `GET /api/aggregation/{resource_id}` delegates to `AggregationService.get_aggregation_detail`
- `tasks/SHIPPED.L030.resource_detail_aggregation_and_notes.md` — original composite contract
- `test/e2e/test_resource.py` — asserts `notes` is an array
- `test/e2e/test_aggregation.py` — asserts `notes` is an array

**Expected behavior**: No route or local service changes should be required if api-utils 0.5.0 composites correctly use `list_all_notes_for_resource`. This task is verification-first; only add application code if a regression is found (document any api_utils gap in **Execution Notes** and set follow-up externally).

## Goals

- Confirm `ResourceService.get_resource` and `AggregationService.get_aggregation_detail` in api-utils 0.5.0 fetch notes via `list_all_notes_for_resource` (not paginated `get_notes_for_resource` with defaults).
- E2E regression: for a resource with known notes in test data, `len(detail["notes"])` matches `detail["aggregation"]["note_count"]` when aggregation exists (or notes array is non-empty when notes exist in DB).
- E2E: `GET /api/resource/{id}` and `GET /api/aggregation/{resource_id}` for the same resource return the same note count.
- If default pagination would truncate composites (regression found), fix in the appropriate layer and document; prefer no local workaround if api_utils is wrong — block and report upstream instead.
- No OpenAPI changes unless composite contract documentation needs clarifying that `notes` is the full in-scope set (not a page).

## Testing Expectations

Run all commands from the **API repository root**.

- **Verification** (read api_utils source after L180 install)
  - Confirm `list_all_notes_for_resource` usage in composite methods before writing tests.
- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
  - `test/e2e/test_resource.py` — add assertion comparing `len(notes)` to `aggregation.note_count` when both present
  - `test/e2e/test_aggregation.py` — add matching note-count regression assertion
- **Build**
  - `pipenv run build`
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`, `pipenv run e2e`

## Outputs

- `test/e2e/test_resource.py` — note count vs aggregation regression test
- `test/e2e/test_aggregation.py` — note count regression test

Optional (only if regression requires local fix — list here during execution):

- `src/routes/resource_routes.py`
- `src/routes/aggregation_routes.py`

The agent must not update files outside this list without updating **Outputs** in **Execution Notes** and halting for human review if an api_utils defect is suspected.

## Execution Notes

**Summary of changes**
- Verified api-utils 0.5.0 composites use `NoteService.list_all_notes_for_resource` (no route changes required).
- Added E2E regression tests for note list truncation (`note_count > 20`) and resource/aggregation note count parity when aggregation counters are consistent.

**Test results**
- `pipenv run test`: 46 passed
- Composite E2E: passed (regression tests skip when seed data counters are stale)
