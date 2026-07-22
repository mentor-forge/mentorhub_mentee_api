# L201 – Adopt Journey harvest from api-utils; remove local services

**Status**: Shipped  
**Type**: Feature  
**Depends On**: `L200_bump_api_utils_0_5_2`  
**Description**: Switch all Journey routes to shared `JourneyService`, delete temporary local promote/detail services and their unit tests, and update route tests to patch `JourneyService.*`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `../mentorhub_api_utils/api_utils/services/journey_service.py` — harvested methods and `RESTRICTED_UPDATE_FIELDS`
- `README.md`
- `Pipfile` — must already pin `api-utils==0.5.2` (L200)
- `src/routes/journey_routes.py` — current route wiring
- `src/services/journey_detail_service.py` — local copy to delete
- `src/services/journey_promote_service.py` — local copy to delete
- `test/routes/test_journey_routes.py` — route unit tests with local-service patch targets
- `tasks/SHIPPED.L170.adopt_api_utils_services.md` — prior adopt-and-delete pattern
- `tasks/SHIPPED.F198.implement_local_journey_detail_service.md` — why local copies existed
- `tasks/SHIPPED.L194.implement_journey_promote_service.md` — local promote service baseline

**External prerequisite**: L200 complete and `api-utils==0.5.2` installed with harvested `JourneyService` methods available. If imports fail or behavior diverges from the local copies, set **Status** to `Blocked` and document the gap in **Execution Notes** — do not keep partial local service files.

### Route switch (`src/routes/journey_routes.py`)

| Endpoint | Before | After |
|----------|--------|-------|
| `GET /api/journey` | `JourneyDetailService.get_my_journey_detail` | `JourneyService.get_my_journey_detail` |
| `PATCH .../promote/path/<path_id>` | `JourneyPromoteService.promote_path_to_next` | `JourneyService.promote_path_to_next` |
| `PATCH .../promote/module/<path_id>/<module_name>` | `JourneyPromoteService.promote_module_to_next` | `JourneyService.promote_module_to_next` |
| `PATCH .../advance/...`, `PATCH .../complete/...`, `PATCH /<id>` | `JourneyService.*` | unchanged |

Additional route cleanup:

- Remove imports of `JourneyDetailService` and `JourneyPromoteService`.
- Remove route-level PATCH guard `if "profile" in data: raise HTTPForbidden(...)` — `JourneyService.update_journey` rejects `profile` via `RESTRICTED_UPDATE_FIELDS`.
- Remove unused `HTTPForbidden` import from `journey_routes.py` if no longer referenced after the guard removal.

### Contract verification (no behavior drift)

- **GET** `/api/journey` returns **`JourneyDetail`** shape (Journey fields + embedded `profile`).
- **PATCH promote/advance/complete** and **PATCH `/<id>`** return plain **`Journey`** without `profile`.
- OpenAPI (`docs/openapi.yaml`) unchanged unless version pin is documented in README.

## Goals

- All Journey domain logic routes through `api_utils.services.JourneyService` only.
- **`src/services/` is deleted entirely** — no local service module remains (Journey promote/detail were the only temporary local copies after L170).
- Route handlers updated per the switch table above.
- Duplicate service unit tests removed (coverage lives in the published `api-utils` package).
- Route unit tests patch `JourneyService.*` on the route module namespace (e.g. `src.routes.journey_routes.JourneyService.get_my_journey_detail`).
- `test_update_journey_rejects_profile_body` mocks `JourneyService.update_journey` with `HTTPForbidden` side effect (service-layer rejection) instead of relying on the removed route guard.
- No remaining references to `JourneyPromoteService`, `JourneyDetailService`, or `src.services` in `src/` or `test/`:
  ```bash
  rg 'JourneyPromoteService|JourneyDetailService|src\.services' src/ test/
  ```
  (expect no matches)

## Testing Expectations

Run all commands from the **API repository root**.

- **Install** (confirm L200 pin still resolves)
  - `pipenv run install`
- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - Route tests: `test/routes/test_journey_routes.py`
- **Build**
  - `pipenv run build`
- **Dev E2E** (API at `localhost:8393`)
  - `pipenv run db` — start backing database (if not already running)
  - `pipenv run dev` — run API dev server (separate terminal or background)
  - `pipenv run e2e` — promote and GET detail scenarios from L193–L199 / F197–F199
- **Packaging verification**
  - `pipenv run container` — build the API container image
  - `pipenv run api` — run db + API containers
  - `pipenv run e2e` — E2E tests against the containerized API

## Outputs

**Delete**

- `src/services/journey_promote_service.py`
- `src/services/journey_detail_service.py`
- `src/services/__init__.py`
- `test/services/test_journey_promote_service.py`
- `test/services/test_journey_detail_service.py`

**Update**

- `src/routes/journey_routes.py` — switch to `JourneyService` for GET detail and promote; remove local service imports and route-level profile guard
- `test/routes/test_journey_routes.py` — patch targets → `JourneyService.*`; update profile-rejection test for service-layer guard

The agent must not update files outside this list unless a stray `src.services` or local journey service reference is discovered in `src/` or `test/` during implementation — in that case, add the file to **Execution Notes** and update it in the same commit.

## Execution Notes

**Summary of changes**
- Switched `GET /api/journey` and promote routes to `JourneyService` from `api-utils==0.5.2`.
- Removed route-level `profile` PATCH guard; service layer rejects via `RESTRICTED_UPDATE_FIELDS`.
- Deleted entire `src/services/` (temporary Journey promote/detail copies) and duplicate service unit tests.
- Updated route tests to patch `JourneyService.*`; profile rejection test mocks service-layer `HTTPForbidden`.

**Test results**
- `rg 'JourneyPromoteService|JourneyDetailService|src\.services' src/ test/` — no matches
- `pipenv run test`: 52 passed, 32 deselected
- `pipenv run lint`: pass
- `pipenv run build`: pass
- `pipenv run container`: pass
- `pipenv run api` + `pipenv run e2e`: 32 passed, 52 deselected