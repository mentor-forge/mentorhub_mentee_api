# Harvest Journey promote mutations into api-utils

**Status**: Open

## Summary

`mentorhub_mentee_api` implements later→next promote mutations **locally** in `src/services/journey_promote_service.py` so the feature can ship without waiting on a new `api-utils` release. The logic should be **harvested** into `api_utils.services.journey_service` following the R046 pattern.

| Mutation | Behavior |
|----------|----------|
| **Promote Path to Next** | Copy **all** `Path.modules[]` onto Journey `next[]`; remove Path id from `journey.later[]`. |
| **Promote Module to Next** | Copy **one** module (by `module_name`) onto `journey.next[]`; keep Path id in `later[]`. Reject duplicate module names in `next` (`400`). |

## Source (this repo)

Harvest from:

- `src/services/journey_promote_service.py` — `JourneyPromoteService.promote_path_to_next`, `promote_module_to_next`, and private helpers
- `test/services/test_journey_promote_service.py` — port tests to `mentorhub_api_utils/tests/services/test_journey_service.py`

## Upstream work (`mentorhub_api_utils`)

1. Move methods onto `JourneyService` (merge helpers into existing class; drop separate `JourneyPromoteService` class name).
2. Add unit tests alongside existing advance/complete coverage.
3. Export methods via `api_utils.services` / top-level `api_utils` if needed.
4. Publish new **`api-utils`** patch/minor to CodeArtifact.

## Follow-on (this repo)

After upstream ships, run **`ISSUE.mentorhub_api_utils.adopt_journey_promote_from_api_utils.md`** — bump pin, switch routes to `JourneyService`, delete local service + duplicate tests.

Unblocks mentee SPA L117 (`adoptJourneyPath`) and L120 Promote button once L193–L196 ship in this repo.
