# F209 - Bump api-utils to 1.0.1 (`token.display_name`)

**Status:** Pending  
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
