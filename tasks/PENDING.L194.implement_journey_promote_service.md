# L194 – Implement local JourneyPromoteService (later → next)

**Status**: Pending  
**Type**: Feature  
**Depends On**: L193  
**Description**: Add `src/services/journey_promote_service.py` with `promote_path_to_next` and `promote_module_to_next` — local implementation to ship before api-utils harvest (see `ISSUE.mentorhub_api_utils.harvest_journey_promote_mutations.md`).

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — promote operations from L193
- `../mentorhub_api_utils/api_utils/services/journey_service.py` — RBAC and mutation patterns (`advance_resource`, `get_my_journey`)
- `tasks/ISSUE.mentorhub_api_utils.harvest_journey_promote_mutations.md`
- `tasks/SHIPPED.L140.implement_journey_advance.md`

## Goals

- **`JourneyPromoteService`** in `src/services/journey_promote_service.py`:
  - All MongoDB I/O via **`MongoIO`**; journey load via **`JourneyService.get_my_journey`**.
  - **`promote_path_to_next(path_id, token, breadcrumb)`** — RBAC same as advance (`profile_id` on token); validate ObjectId; load Path; require id in `later[]`; append all Path modules to `next[]`; remove from `later[]`; persist; return Journey. No Event creation.
  - **`promote_module_to_next(path_id, module_name, token, breadcrumb)`** — same setup; find module by exact `name`; reject duplicate module name already in `next` (`400`); append one module; leave Path in `later[]`.
  - Private helpers: normalize ids, Path module → next-module shape (resource ids as 24-char hex strings).
- **Unit tests** in `test/services/test_journey_promote_service.py` — success and error paths for both methods (mock `MongoIO`, `JourneyService.get_my_journey`).

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_journey_promote_service.py`
- **Build**
  - `pipenv run build`

## Outputs

- `src/services/journey_promote_service.py` — new local service (harvest candidate)
- `src/services/__init__.py` — export `JourneyPromoteService` if needed
- `test/services/test_journey_promote_service.py` — unit tests

The agent must not update files outside this list.

## Execution Notes

_Reserved for the task execution agent._
