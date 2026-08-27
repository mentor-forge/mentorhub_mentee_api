# F207 – JourneyService subclass (Mentee control)

**Status:** Shipped  
**Type:** Feature  
**Depends On:** `F206_resource_path_event_subclasses`  
**Description:** Restore Journey clone-on-GET, profile enrich, PATCH, promote, advance, and complete on a Mentee subclass of shared `JourneyService`. This is the F-EA12 service work. Shared 1.0.0 keeps `get_journey` (404 if missing or hidden) and `get_journey_progress` only. `complete_resource` calls **local** `AggregationService.add_completion`. Do not switch routes and do not pin in this task.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentee **controls** Journey; Customer and Discovery **consume** it
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — RBAC at the service layer
- `tasks/_PLANNING.md` — MongoIO only
- `README.md`
- `../mentorhub_api_utils/README.md` — subclass pattern; inbound writes on the subclass; do not 403 on GET
- `../mentorhub_api_utils/api_utils/services/journey_service.py` — 1.0.0 parent: `get_journey`, `get_journey_progress`, `_oid`, `_validate_object_id`, read `_check_permission`, `TEMPLATE_JOURNEY_ID`
- Full harvest-back class (classmethod form, pre-R078) in `../mentorhub_api_utils/tasks/SHIPPED_ISSUE.journey_api.md` (section **Harvest-back source**). Also `git -C ../mentorhub_api_utils show 9af2886:api_utils/services/journey_service.py`.
- Port tests from the same commit:
  - `git -C ../mentorhub_api_utils show 9af2886:tests/services/test_journey_service.py`
  - `git -C ../mentorhub_api_utils show 9af2886:tests/services/test_journey_service_integration.py`
- `src/services/aggregation_service.py` — `add_completion`
- `src/services/event_service.py` — local `create_event` (advance/complete events are not link hits; still import the local class so F208 does not rewrite internals)
- `docs/openapi.yaml` — `GET /api/journey` is `JourneyDetail`; PATCH mutations return plain `Journey`

**MongoDB I/O:** All Journey writes go through MongoIO (`create_document`, `update_document`, `get_document`). Encode ids with `encode_document` immediately before MongoIO. Do not call PyMongo via `mongo.get_collection(...)`.

**Pattern:**

```python
# src/services/journey_service.py
from api_utils.services import JourneyService as SharedJourneyService
from api_utils.services.journey_service import TEMPLATE_JOURNEY_ID

class JourneyService(SharedJourneyService):
    ...
```

Paste the harvest-back class body from `SHIPPED_ISSUE.journey_api.md`. Align names to the 1.0.0 parent already in `../mentorhub_api_utils` (`MongoIO.get_instance()`, `HTTPBadRequest` / `HTTPForbidden` / `HTTPNotFound` / `HTTPInternalServerError`, `_oid`, `_validate_object_id`, `get_journey`). Parent `get_journey` raises `HTTPNotFound` when missing or hidden — `get_my_journey` clones in that case.

**Change these harvest-back imports:**

- `complete_resource`: `from src.services.aggregation_service import AggregationService` (already in the pasted source).
- Advance/complete `EventService.create_event`: `from src.services.event_service import EventService` (not `api_utils.services.event_service`).

**Shared vs local:**

| On `api_utils.services.JourneyService` | On Mentee subclass |
| --- | --- |
| `get_journey`, `get_journey_progress` | `_clone_template`, `get_my_journey`, `get_my_journey_detail` |
| `_oid`, `_validate_object_id` | `create_journey`, `update_journey` |
| `TEMPLATE_JOURNEY_ID` (import) | `advance_resource`, `complete_resource`, promote* |
| read `_check_permission` | write `_check_permission` (`update` / `mutate` / `complete`) |

**Inbound RBAC:** keep harvest-back `_check_permission` for `update` / `mutate` / `complete` / template clone. Do **not** 403 on GET in this subclass. Admin remains root (`ROLE_ADMIN` / `"admin" in roles` already bypasses update in the harvest-back). `get_my_journey` is **not** on the parent.

This repo has **no** live-Mongo service integration target (`pipenv run test` excludes `@pytest.mark.e2e`). Port `test_journey_service.py` as unit tests with mocked MongoIO. Port integration cases from `test_journey_service_integration.py` the same way (mock MongoIO for clone validity, advance/complete, promote) rather than adding a new live-DB runner.

Do **not** edit `src/routes/journey_routes.py` or `Pipfile` in this task.

## Goals

- `src/services/journey_service.py` exists and subclasses `api_utils.services.JourneyService`.
- Clone-on-GET, profile enrich, create, PATCH, promote, advance, and complete live on the subclass.
- `get_my_journey_detail` returns Journey + embedded `profile`; mutate methods return plain Journey.
- Inbound write checks match the harvest-back; GET visibility stays outbound 404 on the parent.
- Unit tests cover get_my_journey clone, update RBAC, advance, complete, promote, get_my_journey_detail.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_journey_service.py` — clone on `HTTPNotFound` from `get_journey`; update RBAC (owner/admin vs other); restricted fields; advance/complete/promote happy paths and 404 when the resource/path is out of scope; `get_my_journey_detail` embeds `profile`; `complete_resource` calls local `AggregationService.add_completion`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8393/docs/openapi.yaml` — still served

## Outputs

- `src/services/journey_service.py`
- `test/services/test_journey_service.py`

The agent must not update files outside this list.

## Execution Notes

- Created `src/services/journey_service.py` subclassing `SharedJourneyService` with `_clone_template`, `get_my_journey`, `get_my_journey_detail`, `create_journey`, `update_journey`, `advance_resource`, `complete_resource`, `promote_path_to_next`, `promote_module_to_next`, `_validate_object_id`, and `_oid`.
- Created `test/services/test_journey_service.py` porting unit tests covering get_my_journey clone, update RBAC, advance, complete, promote, and get_my_journey_detail.
- Ran `pipenv run test`, `pipenv run lint`, and `pipenv run build` with all 95 unit tests passing.
