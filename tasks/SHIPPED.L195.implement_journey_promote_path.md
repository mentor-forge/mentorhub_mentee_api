# L195 – Implement PATCH /api/journey/promote/path/{path_id} (later → next, all modules)

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L194  
**Description**: Add `PATCH /api/journey/promote/path/{path_id}` route calling local `JourneyPromoteService.promote_path_to_next`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `README.md`
- `docs/openapi.yaml` — `PATCH /api/journey/promote/path/{path_id}` from L193
- `src/services/journey_promote_service.py` — from L194
- `src/routes/journey_routes.py`
- `tasks/SHIPPED.L140.implement_journey_advance.md`

Additional inputs:

- `test/routes/test_journey_routes.py`
- `test/e2e/test_journey.py` — optional promote-path scenario

## Goals

- **`journey_routes.py`**: `PATCH "/promote/path/<path_id>"` → `JourneyPromoteService.promote_path_to_next`; register before `PATCH "/<journey_id>"`.
- **Route unit tests** — success and error propagation.
- **E2E** (optional): promote Path from `later`; assert modules in `next`, Path removed from `later`.

## Testing Expectations

- `pipenv run test`, `pipenv run lint`, `pipenv run build`
- Optional: `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
- Packaging: `pipenv run container`, `pipenv run api`

## Outputs

- `src/routes/journey_routes.py`
- `test/routes/test_journey_routes.py`
- `test/e2e/test_journey.py` — optional E2E

## Execution Notes

**Summary**
- Added `PATCH /api/journey/promote/path/<path_id>` route; registered before `PATCH /<journey_id>`.

**Testing**
- `test/routes/test_journey_routes.py::test_promote_journey_path_success`: pass.
- E2E promote-path scenario deferred (no dedicated E2E yet; existing journey E2E unchanged).
