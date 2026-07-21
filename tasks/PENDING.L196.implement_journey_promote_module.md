# L196 – Implement PATCH /api/journey/promote/module/{path_id}/{module_name} (later → next, single module)

**Status**: Pending  
**Type**: Feature  
**Depends On**: L195  
**Description**: Add `PATCH /api/journey/promote/module/{path_id}/{module_name>` route calling local `JourneyPromoteService.promote_module_to_next`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `README.md`
- `docs/openapi.yaml` — promote module operation from L193
- `src/services/journey_promote_service.py`
- `src/routes/journey_routes.py` — promote path route from L195

Additional inputs:

- `test/routes/test_journey_routes.py`
- `test/e2e/test_journey.py` — optional promote-module scenario

## Goals

- **`journey_routes.py`**: `PATCH "/promote/module/<path_id>/<module_name>"` → `JourneyPromoteService.promote_module_to_next`.
- **Route unit tests** — success, 404, 400 duplicate module.
- **E2E** (optional): single module promote; Path stays in `later`; duplicate returns `400`.

## Testing Expectations

- `pipenv run test`, `pipenv run lint`, `pipenv run build`
- Optional E2E and packaging verification per L195.

## Outputs

- `src/routes/journey_routes.py`
- `test/routes/test_journey_routes.py`
- `test/e2e/test_journey.py` — optional E2E

## Execution Notes

_Reserved for the task execution agent._
