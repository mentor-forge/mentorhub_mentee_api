# F204 – NoteService subclass (`create_note`)

**Status:** Pending  
**Type:** Feature  
**Depends On:** `F203_openapi_1_0_0_consume_gets`  
**Description:** Recreate `src/services/` and a Mentee `NoteService` subclass that restores `create_note` (stripped from api-utils in R079). Inbound create requires the mentee role and `profile_id == token.profile_id`. Do not switch routes and do not pin 1.0.0 — existing Note POST still uses `api_utils.services` until F208.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentee **controls** Note
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer; one collection per service
- `tasks/_PLANNING.md` — MongoIO only; encode ids at the MongoIO boundary
- `README.md`
- `../mentorhub_api_utils/README.md` — subclass pattern; outbound GET RBAC stays on the shared class; inbound write checks on the subclass; routes will import the local class in F208
- `../mentorhub_api_utils/api_utils/services/note_service.py` — 1.0.0 parent: read `_check_permission`, `get_notes_for_resource`, `list_all_notes_for_resource`; `NOTE_LIST_FILTERS` / `NOTE_LIST_ORDER`; `ID_PROPERTIES` is not on the parent — harvest-back used `["_id", "resource_id", "profile_id"]`
- Harvest-back (classmethod form) at git commit `9af2886` in `../mentorhub_api_utils`:
  - `git -C ../mentorhub_api_utils show 9af2886:api_utils/services/note_service.py` — `create_note`
- `../mentorhub_api_utils/tasks/SHIPPED_ISSUE.mentorhub_mentee_api.extend_shared_services.md` — F-EA13 inbound table and harvest snippet
- `docs/openapi.yaml` — Note create subset from F203 (system fields omitted on input)

**MongoDB I/O:** Use `MongoIO` (`get_document`, `get_documents`, `create_document`, `update_document`, `upsert_document`) or inherited shared methods. Encode string ids with `encode_document` immediately before MongoIO. Do not call PyMongo via `mongo.get_collection(...)`. Do not stringify ObjectIds for output.

**Do not** import service classes into routes in this task. **Do not** change `Pipfile`.

Harvest-back `create_note` (adapt imports to 1.0.0 names already used in this repo: `MongoIO.get_instance()`, `HTTPForbidden`, `HTTPInternalServerError`, `encode_document`):

```python
ID_PROPERTIES = ["_id", "resource_id", "profile_id"]

@classmethod
def create_note(cls, data, token, breadcrumb):
    try:
        cls._check_permission(token, "create")
        if "_id" in data:
            del data["_id"]
        encode_document(data, ["_id", "resource_id", "profile_id"], [])
        data["created"] = breadcrumb
        data["saved"] = breadcrumb
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
        note_id = mongo.create_document(config.NOTE_COLLECTION_NAME, data)
        if "_id" not in data:
            from bson import ObjectId
            data["_id"] = ObjectId(note_id)
        return data
    except HTTPForbidden:
        raise
    except Exception as e:
        raise HTTPInternalServerError(f"Failed to create note: {e}")
```

Stamp or require `data["profile_id"] == token["profile_id"]` so a mentee cannot create a note for another profile. Admin (`ROLE_ADMIN` / `"admin" in roles`) is root.

## Goals

- Add `src/services/__init__.py` if missing.
- `src/services/note_service.py`:

```python
from api_utils.services import NoteService as SharedNoteService

class NoteService(SharedNoteService):
    """Mentee Note control: inbound create. List/read stay on the parent."""
```

- Override `_check_permission` so `create` requires `Config.ROLE_MENTEE` in `token["roles"]` (admin is root). Do **not** 403 on `read` — outbound filters stay on the parent.
- Restore `create_note` from the harvest-back. Inherited `get_notes_for_resource` / `list_all_notes_for_resource` stay unchanged.
- Unit tests mock MongoIO; they do not require a live database and must pass while the process still pins `api-utils==0.5.2`.
- Existing `src/routes/note_routes.py` still imports `api_utils.services.NoteService` (F208 switches it).

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_note_service.py` — `create_note` allowed for mentee with matching `profile_id`; `HTTPForbidden` without mentee/admin; admin allowed; `profile_id` cannot be forged to another user; inherited list methods still exist on the subclass
- **Packaging verification** (no HTTP change)
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8393/docs/openapi.yaml` — still served

## Outputs

- `src/services/__init__.py`
- `src/services/note_service.py`
- `test/services/test_note_service.py`

The agent must not update files outside this list.

## Execution Notes
