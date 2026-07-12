# L130 – Implement PATCH /api/journey RBAC (ownership or admin)

**Status**: Shipped  
**Type**: Feature  
**Depends On**: L120  
**Description**: Enforce RBAC on `PATCH /api/journey/{journey_id}`: caller must own the journey (`journey_id` equals token `profile_id`) or have `admin` in token `roles`. Align update payload validation with the L110 OpenAPI `JourneyUpdate` contract.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `../mentorhub_api_utils/README.md`
- `README.md`
- `docs/openapi.yaml` — `PATCH /api/journey/{journey_id}` contract from L110
- `src/services/journey_service.py` — `update_journey`, placeholder `_check_permission`
- `src/routes/journey_routes.py` — `update_journey` route handler
- `api_utils.Config` — `ROLE_ADMIN` or equivalent role string used in this API (default `"admin"` in dev tokens)
- `tasks/SHIPPED.L020.simplify_resource_list_pagination.md` — RBAC pattern reference (admin vs non-admin filtering)

Additional inputs:

- `test/services/test_journey_service.py`
- `test/routes/test_journey_routes.py`

**External prerequisite**: Seeded Journey `_id` == `profile_id` alignment is tracked in [mentorhub_mongodb_api#45](https://github.com/mentor-forge/mentorhub_mongodb_api/issues/45). RBAC unit tests use mocks; E2E ownership scenarios against legacy seed data may defer until that issue ships.

## Goals

- **`JourneyService._check_permission(token, operation, journey_id=None)`** — implement real RBAC:
  - For `operation == 'update'`: allow when `journey_id == token.get('profile_id')` **or** `'admin' in token.get('roles', [])`; otherwise raise `HTTPForbidden`.
  - For `operation == 'read'`: any authenticated user (unchanged).
  - For `operation == 'create'`: keep existing behavior or restrict to staff/admin if POST remains (out of scope unless tests fail).
- **`JourneyService.update_journey`**:
  - Call `_check_permission(token, 'update', journey_id=journey_id)` before mutating.
  - Reject updates to server-managed fields: `_id`, `profile_id`, `created`, `saved`, `library`, `now`, `next` (raise `HTTPForbidden` or strip — prefer reject to match OpenAPI).
  - Allow patching `status` and `later` per OpenAPI `JourneyUpdate`.
  - Continue updating `saved` breadcrumb on successful patch.
- **Unit tests**:
  - Owner (`profile_id` matches `journey_id`) can PATCH allowed fields → `200`.
  - Non-owner non-admin → `403`.
  - Admin with mismatched `journey_id` → `200`.
  - PATCH including `library` / `now` / `next` → `403`.
  - PATCH unknown journey → `404`.
- **Route tests** in `test/routes/test_journey_routes.py` for PATCH success and `403` paths.

## Testing Expectations

Run all commands from the **API repository root**.

- **Unit tests**
  - `pipenv run test`
  - `pipenv run lint`
  - `test/services/test_journey_service.py` — RBAC and field guard tests
  - `test/routes/test_journey_routes.py` — PATCH route RBAC
- **Build**
  - `pipenv run build`
- **Dev E2E** (optional)
  - `pipenv run db`, `pipenv run dev`, `pipenv run e2e`
- **Packaging verification**
  - `pipenv run container`, `pipenv run api`

## Outputs

Paths are relative to the **API repository root**.

- `src/services/journey_service.py` — RBAC implementation and update field guards
- `test/services/test_journey_service.py` — PATCH RBAC unit tests
- `test/routes/test_journey_routes.py` — PATCH route tests

The agent must not update files outside this list.

## Execution Notes

**Summary**
- Implemented `_check_permission` for update (owner or admin).
- Blocked PATCH of server-managed fields (`library`, `now`, `next`, etc.).
- Added RBAC unit and route tests.

**Testing**
- `pipenv run test`: RBAC tests passed.
