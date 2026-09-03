# Mentor Hub — Mentee API

## Current State
Guidance for LLM Code Assistants - NOTE: We are currently pre-release. At this time, no changes should consider backward compatibility. Likewise, while we anticipate versioning releases in the future at this point, no consideration should be given to bumping any versions beyond managing the internal api_utils spa_utils dependencies. We are in a rapid iteration phase where features can be deprecated and removed without pause. When working in this repo we should keep our eyes out for potential re-usable code that could be migrated to api_utils. This code should be implemented locally, and issues opened in the api_utils repo when it is time to migrate code.

Domain services are implemented locally under `src/services/` as subclasses extending the **`api-utils`** 1.0.1 package (`api_utils.services`):
- `JourneyService`: Mentee controls Journey (get-or-create, profile enrich, PATCH promote/advance/complete).
- `NoteService`: Inbound RBAC for creating notes (`POST /api/note`).
- `AggregationService`: Metrics calculation (`add_hit`, `add_completion`, `get_aggregation_detail`).
- `ResourceService`: Mentee BFF composite `get_resource` (`{resource, aggregation, notes}`).
- `PathService`: Nested topic resource summary enrichment.
- `EventService`: Triggers `AggregationService.add_hit` on link events.

Basic Service code should be single-collection aligned. Complex services that need to combine data from multiple single-collection services can be created when needed. Intra-Service dependencies should follow the flow from the [Data ERD](https://github.com/mentor-forge/mentorhub_mongodb_api/blob/main/erd.svg).

## Prerequisites
- Mentor Hub [Developers Edition](https://github.com/mentor-forge/mentorhub/blob/main/CONTRIBUTING.md)
- Developer [API Standard Prerequisites](https://github.com/mentor-forge/mentorhub/blob/main/DeveloperEdition/standards/api_standards.md)

## Developer Commands

```bash
## Install dependencies (run `mh` first for CodeArtifact auth)
pipenv run install

# start backing db container 
# Container Related commands use `de down` before starting the requested containers
pipenv run db

## run unit tests 
pipenv run test

## run api server in dev mode - captures command line, serves API at localhost:8393
pipenv run dev

## run E2E tests (assumes running API at localhost:8393)
pipenv run e2e

## run tests with coverage report
pipenv run coverage

## build application (pre-compiles Python code)
pipenv run build

## build container 
pipenv run container

## Run the backing database and api containers
pipenv run api

## Run the full microservice (db+api+spa)
pipenv run service

## format code
pipenv run format

## lint code
pipenv run lint
```

## Project Structure

- `src/` - Main package containing:
  - `server.py` - API entrypoint
  - `routes/` - HTTP request/response handlers using shared GET route factories and domain endpoints
  - `services/` - Domain service subclasses extending `api_utils.services`
- `test/` - Test suite with matching directory structure:
  - `routes/` - Route unit tests
  - `services/` - Service unit tests
  - `e2e/` - End-to-end tests flagged with `@pytest.mark.e2e`

## API Endpoints

see the [Open API Specifications](./docs/openapi.yaml) for details on the API

For E2E, mint a Bearer token via `test/e2e/e2e_auth.py` (`get_auth_token()`) with `pipenv run dev` (matching `JWT_SECRET`).

### Simple Curl Commands:
```bash
# Bearer token for local dev (same JWT settings as pipenv run dev / e2e):
export TOKEN="$(PYTHONPATH=. pipenv run python -c 'from test.e2e.e2e_auth import get_auth_token; print(get_auth_token())')"

# Get the API Configuration
curl http://localhost:8393/api/config \
  -H "Authorization: Bearer $TOKEN"

```