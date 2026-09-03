# F210 - Replace token `name` with `display_name`

**Status:** Pending  
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
