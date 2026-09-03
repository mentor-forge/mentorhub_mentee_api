# F210 - Replace token `name` with `display_name`

**Status:** Blocked  
**Type:** Feature  
**Depends On:** `F209_bump_api_utils_1_0_1`  
**Description:** Complete the remaining API-side work for [F-ES15 / issue #35](https://github.com/mentor-forge/mentorhub_mentee_spa/issues/35) by replacing caller-token uses of `name` with `display_name` in source, tests, and E2E token minting after the shared library bump is in place.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md`
- `tasks/PENDING.F209.bump_api_utils_1_0_1.md` (or shipped equivalent) - follow the audited installed token contract from that task
- `README.md`
- `../mentorhub_api_utils/README.md`
- `../mentorhub_api_utils/api_utils/flask_utils/token.py` - use for source orientation only; the installed `1.0.1` package remains the execution source of truth
- `test/e2e/e2e_auth.py`
- `src/routes/`
- `src/services/`
- `test/routes/`
- `test/services/`

**Source issue:** [F-ES15: Display Name](https://github.com/mentor-forge/mentorhub_mentee_spa/issues/35).

Current planning audit found this repo still mints JWTs with a `name` claim in `test/e2e/e2e_auth.py`, while direct token-field reads in `src/` were not immediately evident. Confirm with grep before editing so the task only changes real token-contract usage.

**Do not change:** domain document `name` fields, OpenAPI model property names, list query parameters named `name`, Flask blueprint names, or unrelated string keys.

## Goals

- Zero remaining caller-token reads or writes of `name` in this repo once `api-utils==1.0.1` is installed.
- `test/e2e/e2e_auth.py` mints JWT claims that map cleanly to the `display_name` field exposed by the installed token contract.
- Any mock token dicts representing `create_flask_token()` output in unit tests use `display_name` instead of `name`.
- Any assertions on copied token context, breadcrumbs, or route/service inputs are updated to the `display_name` contract where appropriate.
- README token examples or narrative, if any remain after F209, are consistent with `display_name`.
- MongoDB I/O in any touched services remains on `MongoIO`.

### Craftsmanship Expectations

- Prefer deleting obsolete token `name` usage rather than carrying both keys.
- Do not create a local fallback like `token.get("display_name") or token.get("name")`.
- Keep the scope limited to authenticated caller-token data; document/resource `name` stays unchanged.
- If grep confirms only E2E auth payloads and token fixtures need updates, keep the code change set narrow.

## Testing Expectations

Run all commands from this API repository root.

- Confirmation grep for token usage:
  - `rg 'token\.name' src test`
  - `rg 'token\[\"name\"\]|token\[\'name\'\]|token\.get\(\"name\"\)|token\.get\(\'name\'\)' src test`
  - `rg '\"name\":|name=' test/e2e/e2e_auth.py test/routes test/services` and manually distinguish token claims from unrelated domain fields
- `rg 'display_name' test/e2e/e2e_auth.py test/routes test/services` should show the updated token-contract usage
- `pipenv run test`
- `pipenv run lint`
- `pipenv run build`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`
- Boundary check: existing authorization behavior must remain intact; only the token display-field contract should change.

## Outputs

- `test/e2e/e2e_auth.py`
- `test/routes/*.py` - only if mock token dicts or assertions use token `name`
- `test/services/*.py` - only if mock token dicts or assertions use token `name`
- `src/routes/*.py` - only if a route reads the token display field
- `src/services/*.py` - only if a service reads the token display field
- `README.md` - only if token documentation still mentions `name`

The agent must not update files outside this list. Skip files that do not contain caller-token `name` usage after the audit.

## Execution Notes

### Plan
1. Confirm F209 installed contract: `Token.to_dict()` / `create_flask_token()` expose application key `display_name` only (JWT `name` first, then JWT `display_name`, then `""`). Shared `EventService.create_event` copies `dict(token)` into Event `context`.
2. Audit caller-token `name` usage (do not rename domain document `name`, list `?name=`, OpenAPI, or blueprint names):
   - `src/routes/` and `src/services/` — no `token["name"]` / `token.get("name")` / `token.name`. Skip src.
   - `README.md` — no token `name` documentation. Skip.
   - `test/e2e/e2e_auth.py` — mints OIDC JWT `name`. Replace with JWT `display_name` so the mint maps cleanly to the application field (1.0.1 accepts either wire claim). Delete the `name` parameter; do not keep both keys or a local fallback.
   - `test/routes/` and `test/services/` — mock flask-token dicts omit both keys (F209 left rewrites here). Add `display_name` to fixtures that represent `create_flask_token()` output; never add token `name`. Leave document/list `name` and incomplete negative-case inline tokens unchanged.
3. Do **not** edit `test/e2e/test_event.py` (out of Outputs). Its `context.get("name")` assertion is expected to keep packaging e2e red.
4. Do not change `Pipfile` / `Pipfile.lock`. MongoIO-only I/O stays as-is (src untouched).
5. Run confirmation greps, `pipenv run test`, `lint`, `build`, then packaging `container` / `api` / `e2e`. Ship only if in-scope required gates pass; otherwise Blocked.

### Summary
In-scope token-contract rewrite is done. `e2e_auth.py` now mints JWT `display_name` (`Mike Storey`) and no longer writes claim or parameter `name`. Mock flask-token dicts in `test/routes/` and `test/services/` include `display_name` and omit token `name`. `src/routes/`, `src/services/`, and `README.md` skipped (no caller-token `name` usage). Domain document `name`, list `?name=`, and incomplete negative-case inline tokens left unchanged. Pipfile not touched. No local `display_name`/`name` fallback.

### Confirmation greps
- `rg 'token\.name' src test` — zero hits
- `rg 'token\["name"\]|token\[\'name\'\]|token\.get\("name"\)|token\.get\(\'name\'\)' src test` — zero hits
- `rg '"name":' test/e2e/e2e_auth.py` — zero hits
- `rg 'display_name' test/e2e/e2e_auth.py test/routes test/services` — mint + mock-token usage present

Remaining `"name":` / `name=` in `test/routes` and `test/services` (false positives, not token dicts):
- Path / Resource / Journey / Profile **document** fixtures (`"name": "path1"`, `"name": "Test Resource"`, module/topic names)
- List filters (`?name=onboard`, `?name=guide`, `{"name": "guide"}`)
- Journey PATCH bodies that reject a Profile document `name` field
- `test_journey_service.py` Path/Resource/module document names

### Test results
- **Unit:** `pipenv run test` — 98 passed, 36 deselected
- **Lint:** `pipenv run lint` — passed (38 files unchanged)
- **Build:** `pipenv run build` — passed
- **Packaging:** `pipenv run container` built `ghcr.io/mentor-forge/mentorhub_mentee_api:latest` with `api-utils==1.0.1`. `pipenv run api` started the mentee-api stack.
- **E2E:** 35 passed, 1 failed:
  - Passed: aggregation, journey, note, path, resource, event GET/auth/client-context-ignored, remaining create-event assertions (`user_id`, `roles`, `profile_id`, `customer_id`, `mentor_id`, `remote_ip`). JWT `display_name` maps to token `display_name`. Unauthorized flows still 401.
  - Failed: `test/e2e/test_event.py::test_create_event_endpoint` asserts `context.get("name") == "Mike Storey"`. Live context has `display_name: "Mike Storey"` and no `name`.

### Blocker
Packaging e2e is a required gate and failed solely on Event context asserting the old application-token `name` key. That assertion lives in `test/e2e/test_event.py`, which is **not** in this task's Outputs. Did not edit that file.

Follow-up: add `test/e2e/test_event.py` to a follow-on task (or expand Outputs) and assert `context.display_name` instead of `context.name`. In-scope F210 rewrite is implemented; do not treat this as Shipped until the e2e gate is green.
