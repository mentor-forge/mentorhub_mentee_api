# Adopt api-utils Journey promote mutations and remove local service

**Status**: Open (blocked on harvest)

## Summary

After **`ISSUE.mentorhub_api_utils.harvest_journey_promote_mutations.md`** ships a new `api-utils` release with `JourneyService.promote_path_to_next` and `JourneyService.promote_module_to_next`, this repo should drop the temporary local implementation.

## Goals

1. **Bump dependency**
   - Pin `api-utils` to the release that includes promote methods.
   - `pipenv run install`; refresh `Pipfile.lock`.

2. **Switch routes**
   - `src/routes/journey_routes.py` — import `JourneyService` from `api_utils.services`; call `JourneyService.promote_path_to_next` / `promote_module_to_next` instead of `JourneyPromoteService`.

3. **Remove local copies**
   - Delete `src/services/journey_promote_service.py`
   - Delete `src/services/__init__.py` if the directory becomes empty
   - Delete `test/services/test_journey_promote_service.py`
   - Keep route tests in `test/routes/test_journey_routes.py` (patch targets become `JourneyService.*`).

4. **Verify**
   - `pipenv run test`, `pipenv run lint`, `pipenv run build`
   - `pipenv run container`, `pipenv run api`, `pipenv run e2e`

## Notes

- OpenAPI (`docs/openapi.yaml`) and E2E promote scenarios from L193–L196 should remain unchanged — only the service import path changes.
- Do not run until the harvest ISSUE is resolved and the version is published to CodeArtifact.
