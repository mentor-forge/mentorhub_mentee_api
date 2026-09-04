# F209 - Bump api-utils to 1.0.1 (`token.display_name`)

**Status:** Blocked  
**Type:** Feature  
**Depends On:** none  
**Description:** Implement the API-side dependency work needed for [F-ES15 / issue #35](https://github.com/mentor-forge/mentorhub_mentee_spa/issues/35): pin `api-utils` to `1.0.1`, audit the installed token contract, and align this API with the shared `display_name` token field without renaming domain document `name` fields.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md`
- `../mentorhub/DeveloperEdition/standards/api_standards.md`
- `tasks/_PLANNING.md` - Shared Library / Version Bump Checklist and packaging gate
- `tasks/_ORCHESTRATE.md`
- `README.md`
- `../mentorhub_api_utils/README.md`
- `Pipfile`
- `Pipfile.lock`
- `test/e2e/e2e_auth.py`
- `src/routes/` - routes use `create_flask_token()` and must consume the installed token dict contract
- `src/services/` - confirm any token display-field reads and preserve MongoIO-only access
- `test/routes/` and `test/services/` - token fixtures or assertions representing `create_flask_token()` output

**Source issue:** [F-ES15: Display Name](https://github.com/mentor-forge/mentorhub_mentee_spa/issues/35) - bump shared utils and replace token `name` with `display_name`.

**External prerequisite:** `api-utils==1.0.1` must resolve from CodeArtifact using `pipenv run install`. If `1.0.1` cannot be installed, mark this task Blocked and stop. Do not substitute a sibling checkout or a loose version range.

**Token vs document name:** Only the authenticated caller token contract is changing. Do not rename Mentee domain document fields, OpenAPI schema properties, list filters, route names, or other unrelated `name` usages.

## Goals

- `Pipfile` and `Pipfile.lock` pin `api-utils==1.0.1`.
- Dependencies are refreshed with `pipenv run install` rather than bare `pipenv install`.
- The installed `api_utils.flask_utils.token.Token` contract is audited so execution notes record whether `display_name` is sourced from JWT `display_name`, mapped from another claim, or both.
- Any route or service code that reads the caller token display field is updated to the installed `1.0.1` contract.
- Existing MongoDB access patterns remain on `MongoIO` only; this task must not introduce direct PyMongo calls.
- `README.md` no longer documents `api-utils==1.0.0` once the bump is complete.

### Craftsmanship Expectations

- Treat the installed shared library as the single source of truth for token claim shape.
- Do not add a local compatibility alias that accepts both `name` and `display_name` indefinitely.
- Do not rename domain resource `name` fields to `display_name`.
- If no application code reads the token display field today, keep the implementation minimal and focus on the dependency bump plus contract audit.

## Testing Expectations

Run all commands from this API repository root.

- `mh` once per shell if CodeArtifact credentials are missing
- `pipenv run install`
- Audit the installed token contract, for example by inspecting `api_utils.flask_utils.token.Token.to_dict()` / claim mapping from the installed package
- `pipenv run test`
- `pipenv run lint`
- `pipenv run build`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e`
- Negative/boundary check: authenticated flows must continue to require the JWT claims that `api-utils==1.0.1` expects; do not weaken token validation to preserve older `name` payloads.

## Outputs

- `Pipfile`
- `Pipfile.lock`
- `README.md`
- `src/routes/*.py` - only if a route reads the token display field
- `src/services/*.py` - only if a service reads the token display field
- `test/routes/*.py` - only if token fixtures/assertions need to match `1.0.1`
- `test/services/*.py` - only if token fixtures/assertions need to match `1.0.1`
- `test/e2e/e2e_auth.py` - if the installed token contract requires JWT claim changes as part of the bump

The agent must not update files outside this list.

## Execution Notes

### Plan
1. Pin `Pipfile` `api-utils==1.0.1` (keep single CodeArtifact `[[source]]` and the unrelated-PyPI comment). Refresh `Pipfile.lock` via `scripts/pipenv-lock.sh` then `pipenv run install` (`mh` first if CodeArtifact auth is missing). If 1.0.1 cannot resolve, set Status to Blocked and stop — no sibling path install.
2. After install, audit **installed** `api_utils.flask_utils.token.Token.to_dict` / `create_flask_token()` and helper signatures (`MongoIO`, `parse_list_request`, `encode_document`, exceptions, shared GET factories).
3. Token-display-field audit of this API (pre-change):
   - No `src/routes/` or `src/services/` reads `token["name"]` / `token.get("name")` / `token.name`. Domain document `name` (Journey modules/topics, Path, Resource) stays unchanged.
   - `event_service.py` subclasses shared `create_event` and only reads `token.get("resource_id")` — skip.
   - Mock flask-token fixtures omit both `name` and `display_name`; they are not asserted as `create_flask_token()` output shape. Leave fixture rewrites to F210.
   - `e2e_auth.py` already mints OIDC JWT `name`. Change JWT claims only if installed 1.0.1 requires a different wire claim for validation. Application-dict `display_name` rewrites belong to F210.
   - `README.md`: replace documented `api-utils` 1.0.0 pin with 1.0.1.
4. Skip `src/routes/*.py`, `src/services/*.py`, `test/routes/*.py`, `test/services/*.py`, and `test/e2e/e2e_auth.py` unless the installed contract requires them for the bump itself.
5. Run `pipenv run test`, `lint`, `build`, then `container`, `api`, `e2e`. If an in-scope required gate fails, set Status to Blocked and stop.

### Summary
Pinned `api-utils==1.0.1` from CodeArtifact (`scripts/pipenv-lock.sh` then `pipenv run install`). CodeArtifact credentials were already available (`mh` not required). Installed package version is `1.0.1` from the venv site-packages, not a sibling checkout.

**Installed Token contract (source of truth):** `Token.to_dict()` / `create_flask_token()` return application key `display_name` (no `name` key). Mapping is JWT `name` first, then JWT `display_name`, then `""`. `_map_claims()` still requires `profile_id` and derives `user_id` from `sub`. JWT wire claim does not need to change for validation; `e2e_auth.py` already mints OIDC `name`.

Helper signatures (`MongoIO.get_document` / `get_documents` / `create_document` / `update_document` / `upsert_document`, `encode_document`, `parse_list_request`, HTTP exceptions) match current mentee API usage — no signature fixes required. Shared `EventService.create_event` copies `dict(token)` into Event `context`.

Application token `name` rewrites left to F210. No `src/routes/` or `src/services/` reads the token display field. Domain document `name` fields unchanged. Mock token fixtures still omit both `name` and `display_name`. `e2e_auth.py` unchanged (JWT `name` remains the 1.0.1 wire mapping).

### Test results
- **Install:** `api-utils==1.0.1` resolved and installed from CodeArtifact. Container build also installed `api-utils==1.0.1`.
- **Unit:** `pipenv run test` — 98 passed, 36 deselected.
- **Lint:** `pipenv run lint` — passed (38 files unchanged).
- **Build:** `pipenv run build` — passed.
- **Packaging:** `pipenv run container` built `ghcr.io/mentor-forge/mentorhub_mentee_api:latest` with `api-utils==1.0.1`. `pipenv run api` started the stack.
- **E2E:** 35 passed, 1 failed:
  - Passed: aggregation, journey, note, path, resource, event GET/auth/client-context-ignored, and remaining create-event assertions (`user_id`, `roles`, `profile_id`, `customer_id`, `mentor_id`, `remote_ip`). JWT `name` maps to token `display_name`; unauthorized flows still 401.
  - Failed: `test/e2e/test_event.py::test_create_event_endpoint` asserts `context.get("name") == "Mike Storey"`. Live context has `display_name: "Mike Storey"` and no `name`.

### Blocker
Packaging e2e is a required gate and failed on Event context asserting the old application-token `name` key. That assertion lives in `test/e2e/test_event.py`, which is **not** in this task's Outputs. Changing `e2e_auth.py` cannot restore `context.name` because 1.0.1 `to_dict()` never emits `name`. F210 is the planned rewrite task, but it also does not list `test/e2e/test_event.py`. Did not update that file, did not implement F210, and did not path-install sibling `api_utils`.

Follow-up: add `test/e2e/test_event.py` to F210 Outputs (or a follow-on task) and assert `context.display_name` instead of `context.name`. Token bump itself is implemented; do not treat this as Shipped until the e2e gate is green.
