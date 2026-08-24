# F205 – AggregationService subclass (mutate + detail)

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F204_note_service_subclass`  
**Description:** Restore Mentee aggregation writes and the `{aggregation, notes}` detail composite on a subclass. Shared 1.0.0 keeps `get_aggregation_for_resource` (no create) plus `_find_aggregation` / `_resource_object_id`. Duration helpers are **not** on the parent — copy them onto this subclass. `add_completion` must import **local** `NoteService`. No routes and no pin in this task.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer
- `tasks/_PLANNING.md` — MongoIO only
- `README.md`
- `../mentorhub_api_utils/README.md` — subclass pattern
- `../mentorhub_api_utils/api_utils/services/aggregation_service.py` — 1.0.0 parent: `get_aggregation_for_resource`, `_find_aggregation`, `_resource_object_id` (do not reimplement those; inherit)
- Harvest-back at `9af2886`:
  - `git -C ../mentorhub_api_utils show 9af2886:api_utils/services/aggregation_service.py` — `_parse_iso_duration`, `_format_iso_duration`, `_add_durations`, `_new_aggregation_document`, `_get_or_create_aggregation`, `add_hit`, `add_completion`, `get_aggregation_detail`
- `src/services/note_service.py` — local `create_note` / `list_all_notes_for_resource`
- `docs/openapi.yaml` — `GET /api/aggregation/{resource_id}` still returns `AggregationDetail` (`{aggregation, notes}`)

**MongoDB I/O:** MongoIO only. Encode string ids with `encode_document` immediately before MongoIO. Do not stringify ObjectIds for output.

**Inbound RBAC (writes only):**

| Method | Who may call (non-admin) |
| --- | --- |
| `add_hit` | any authenticated token (current) |
| `add_completion` | mentee role (`Config.ROLE_MENTEE`) |

Admin is root. Do **not** 403 on GET / detail.

`add_completion` in the harvest-back imported `from api_utils.services.note_service import NoteService` — change to `from src.services.note_service import NoteService`. `get_aggregation_detail` uses `NoteService.list_all_notes_for_resource` (inherited on the local subclass).

`complete_resource` on Journey (F207) will call `AggregationService.add_completion`. Keep that method signature identical to the harvest-back (`resource_id`, `rating`, `note`, `duration`, `token`, `breadcrumb`).

## Goals

- `src/services/aggregation_service.py`:

```python
from api_utils.services import AggregationService as SharedAggregationService

class AggregationService(SharedAggregationService):
    """Mentee aggregation mutate + get-or-create detail composite."""
```

- Copy onto the subclass from `9af2886` (do not put these on a fork of the parent):
  - duration helpers `_parse_iso_duration`, `_format_iso_duration`, `_add_durations`
  - `_new_aggregation_document`, `_get_or_create_aggregation`
  - `add_hit`, `add_completion`
  - `get_aggregation_detail` — get-or-create + `NoteService.list_all_notes_for_resource` → `{aggregation, notes}`
- Override `_check_permission` only as needed for `add_hit` / `add_completion` inbound rules. Inherit `get_aggregation_for_resource`.
- Unit tests mock MongoIO and local `NoteService`; no live database.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_aggregation_service.py` — `add_hit` allowed for any authenticated token; `add_completion` requires mentee (admin root); `add_completion` calls local `NoteService.create_note` when a note is provided; `get_aggregation_detail` returns `{aggregation, notes}` and get-or-creates; duration helpers round-trip
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8393/docs/openapi.yaml` — still served

## Outputs

- `src/services/aggregation_service.py`
- `test/services/test_aggregation_service.py`

The agent must not update files outside this list.

## Execution Notes
