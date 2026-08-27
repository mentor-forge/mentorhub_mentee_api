# F206 – Resource, Path, and Event service subclasses

**Status:** Shipped  
**Type:** Feature  
**Depends On:** `F205_aggregation_service_subclass`  
**Description:** Restore Mentee BFF enrich on Resource and Path, and a thin Event subclass that calls local `AggregationService.add_hit` on link events. Shared 1.0.0 `get_resource` / `get_path` return raw documents; `create_event` stays on the parent. Do not switch routes and do not pin — unit tests must mock `super()` so they pass against the still-installed `api-utils==0.5.2`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentee **consumes** Resource and Path (GET only); **creates** Event
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md` — MongoIO only
- `README.md`
- `../mentorhub_api_utils/README.md`
- `../mentorhub_api_utils/api_utils/services/resource_service.py` — 1.0.0 `get_resource` is the raw document; `get_resources` / `get_resources_by_ids` stay inherited
- `../mentorhub_api_utils/api_utils/services/path_service.py` — 1.0.0 `get_path` is the raw Path (no resource enrich)
- `../mentorhub_api_utils/api_utils/services/event_service.py` — shared `create_event` (global POST); `EVENT_TYPE_LINK` is `Config.EVENT_TYPE_LINK`
- Harvest-back at `9af2886`:
  - `git -C ../mentorhub_api_utils show 9af2886:api_utils/services/path_service.py` — `_collect_resource_ids`, `_enrich_path_resources`, enriched `get_path`
  - `git -C ../mentorhub_api_utils show 9af2886:api_utils/services/resource_service.py` — composite `get_resource` (removed later in R083)
  - `git -C ../mentorhub_api_utils show 9af2886:api_utils/services/event_service.py` — after insert, `type == EVENT_TYPE_LINK` and `token.resource_id` → `AggregationService.add_hit`
- `src/services/aggregation_service.py` — `get_aggregation_for_resource`, `add_hit`
- `src/services/note_service.py` — `list_all_notes_for_resource`
- `docs/openapi.yaml` — Resource by-id is `ResourceDetail`; Path by-id is `PathDetail` with nested resource summaries

**MongoDB I/O:** Prefer inherited shared methods. Any new I/O uses MongoIO only.

**Do not** POST Resource or Path here (Mentor **controls** Resource). Do **not** 403 on GET in these subclasses.

**`super()` on 0.5.2:** the installed parent may still enrich. Unit-test overrides by mocking `super().get_resource` / `super().get_path` / `super().create_event` so tests do not depend on parent behavior. F208 pins 1.0.0 and then the wrap is correct in process.

Event wrap (do **not** copy the whole shared `create_event`; call `super()` then the harvest-back link block so parent context-stamping stays in one place):

```python
created = super().create_event(data, token, breadcrumb)
config = Config.get_instance()
if created.get("type") == config.EVENT_TYPE_LINK:
    resource_id = token.get("resource_id")
    if resource_id:
        from src.services.aggregation_service import AggregationService
        AggregationService.add_hit(resource_id, token, breadcrumb)
    else:
        logger.warning(
            "link event created without resource_id in token; skipping add_hit"
        )
return created
```

Path enrich: `path = super().get_path(...)`; `ResourceService.get_resources_by_ids`; `_enrich_path_resources`; return enriched. Use **local** `ResourceService`. Copy helper bodies from `9af2886`.

Resource composite (use **local** Aggregation and Note):

```python
@classmethod
def get_resource(cls, resource_id, token, breadcrumb):
    resource = super().get_resource(resource_id, token, breadcrumb)
    aggregation = AggregationService.get_aggregation_for_resource(
        resource_id, token, breadcrumb
    )
    notes = NoteService.list_all_notes_for_resource(
        resource_id, token, breadcrumb
    )
    return {
        "resource": resource,
        "aggregation": aggregation,
        "notes": notes,
    }
```

## Goals

- `src/services/resource_service.py` — subclass; override `get_resource` with the BFF composite; inherit `get_resources` / `get_resources_by_ids`.
- `src/services/path_service.py` — subclass; copy `_collect_resource_ids` and `_enrich_path_resources`; wrap `get_path`; inherit `get_paths`.
- `src/services/event_service.py` — subclass; override `create_event` as above so link hits go to **local** `AggregationService.add_hit`. Any authenticated caller may create (shared default). Admin is root.
- Unit tests mock `super()` and local collaborators; no live database.

## Testing Expectations

Run all commands from this API repository root.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
  - `test/services/test_resource_service.py` — `get_resource` returns `{resource, aggregation, notes}`; list methods inherited
  - `test/services/test_path_service.py` — `get_path` calls `super().get_path` then enrich; missing nested resources handled
  - `test/services/test_event_service.py` — `create_event` with `EVENT_TYPE_LINK` and `token.resource_id` calls `AggregationService.add_hit`; link without `resource_id` skips add_hit; non-link types do not call add_hit
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `curl -s http://localhost:8393/docs/openapi.yaml` — still served

## Outputs

- `src/services/resource_service.py`
- `src/services/path_service.py`
- `src/services/event_service.py`
- `test/services/test_resource_service.py`
- `test/services/test_path_service.py`
- `test/services/test_event_service.py`

The agent must not update files outside this list.

## Execution Notes

- Created `src/services/resource_service.py` subclassing `SharedResourceService` with composite `get_resource` returning `{resource, aggregation, notes}`.
- Created `src/services/path_service.py` subclassing `SharedPathService` with `_collect_resource_ids`, `_enrich_path_resources`, and wrapped `get_path`.
- Created `src/services/event_service.py` subclassing `SharedEventService` with wrapped `create_event` triggering local `AggregationService.add_hit` on link events.
- Created unit tests: `test/services/test_resource_service.py`, `test/services/test_path_service.py`, and `test/services/test_event_service.py`.
- Ran `pipenv run test`, `pipenv run lint`, and `pipenv run build` with all unit tests passing.
