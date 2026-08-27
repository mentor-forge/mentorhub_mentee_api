# F208 – Pin api-utils 1.0.0 and wire local service routes

**Status:** Shipped  
**Type:** Feature  
**Depends On:** `F207_journey_service_subclass`  
**Description:** F-EA12 owns this pin. Cut over every route module from `api_utils.services` to local subclasses, mount shared `create_*_get_routes` factories, and keep Mentee-local GET/POST/PATCH that the factories do not provide. Lands in the **same PR** as F-EA12 / F-EA13. After this task, no route imports a service class from `api_utils.services`.

## Context

Always read these files before implementation:

- `../mentorhub/DeveloperEdition/standards/ArchitecturePrinciples.md` — Mentee **controls** Journey / Note; **creates** Event; **consumes** Resource / Path (GET only)
- `../mentorhub/DeveloperEdition/standards/api_standards.md` — routes are HTTP-only (token, breadcrumb, exceptions, payload pass-through)
- `tasks/_PLANNING.md` — `pipenv run install` after Pipfile changes (CodeArtifact; run `mh` first)
- `README.md` — currently says domain services come from `api-utils`, not `src/services/`
- `../mentorhub_api_utils/README.md` — `create_*_get_routes(service_cls)` then add POST/PATCH on the returned blueprint; list GET is a JSON array; `offset`/`size` headers only
- `../mentorhub_api_utils/api_utils/routes/shared_get_routes.py`
- `Pipfile` / `Pipfile.lock` — currently `api-utils==0.5.2`
- `src/server.py` — keep existing `/api/*` prefixes; factories return blueprints registered the same way
- `docs/openapi.yaml` — F203 consume GETs plus unchanged control/composite operations
- Local services from F204–F207: `src/services/note_service.py`, `aggregation_service.py`, `resource_service.py`, `path_service.py`, `event_service.py`, `journey_service.py`
- Current routes: `src/routes/journey_routes.py`, `note_routes.py`, `aggregation_routes.py`, `event_routes.py`, `resource_routes.py`, `path_routes.py`
- Route tests under `test/routes/`; patch targets stay `src.routes.<module>.<Service>.*`
- `test/e2e/` — add coverage for the new list/by-id GETs; keep existing POST/PATCH e2e
- `test/e2e/e2e_auth.py` — tokens must include `profile_id` (api-utils 1.0.0 rejects tokens without it)

**External prerequisite:** `api-utils==1.0.0` must resolve from the CodeArtifact index. If `pipenv run install` cannot resolve 1.0.0, set **Status** to `Blocked` and stop.

**Pin:** this task (F-EA12) owns `api-utils==1.0.0`. Install with `pipenv run install`. Do **not** use bare `pipenv install`. Use `scripts/pipenv-lock.sh` if lock hashes must be regenerated first.

**Why pin is last:** 1.0.0 strips Journey mutations and Note/Aggregation/Path/Resource enrich that current routes still call on the shared classes. Subclasses in F204–F207 restore those methods; this task switches imports and then pins so `pipenv run test` stays green.

### Route mapping

| File | After |
| --- | --- |
| `src/routes/resource_routes.py` | `bp = create_resource_get_routes(ResourceService)` — list + by-id; by-id uses subclass composite. **No POST.** |
| `src/routes/path_routes.py` | `bp = create_path_get_routes(PathService)` — list + by-id; by-id uses subclass enrich. **No POST.** |
| `src/routes/note_routes.py` | `bp = create_note_get_routes(NoteService)` then `POST ""` → `NoteService.create_note` (`201`) |
| `src/routes/event_routes.py` | `bp = create_event_get_routes(EventService)` then `POST ""` → `EventService.create_event` (`201`) |
| `src/routes/journey_routes.py` | `bp = create_journey_get_routes(JourneyService)` (by-id GET only) then keep local `GET ""` → `get_my_journey_detail` and existing PATCH promote/advance/complete/`/<journey_id>` |
| `src/routes/aggregation_routes.py` | **Do not** mount `create_aggregation_get_routes` (plain doc). Keep local `GET /<resource_id>` → `get_aggregation_detail` so OpenAPI `{aggregation, notes}` stays. Import **local** `AggregationService`. |

Filter/order constants may still come from `api_utils` via the factory MRO lookup. Do **not** `from api_utils.services import JourneyService` (or Note/Event/Path/Resource/Aggregation service classes) in any route module.

POST/PATCH handlers: `create_flask_token()`, `create_flask_breadcrumb(token)`, `request.get_json() or {}`, `@handle_route_exceptions`. Do not validate or alter payloads in the route.

**Journey HTTP contract (unchanged except new by-id GET from the factory):**

| Endpoint | Local method |
| --- | --- |
| `GET /api/journey` | `JourneyService.get_my_journey_detail` |
| `GET /api/journey/<journey_id>` | inherited `get_journey` (factory) |
| `PATCH /api/journey/promote/path/<path_id>` | `promote_path_to_next` |
| `PATCH /api/journey/promote/module/<path_id>/<module_name>` | `promote_module_to_next` |
| `PATCH /api/journey/advance/<resource_id>` | `advance_resource` |
| `PATCH /api/journey/complete/<resource_id>` | `complete_resource` |
| `PATCH /api/journey/<journey_id>` | `update_journey` |

GET still returns Journey + embedded `profile`; PATCH mutations return plain Journey.

## Goals

- `Pipfile` and `Pipfile.lock` pin `api-utils==1.0.0` (CodeArtifact `[[source]]` unchanged; keep the comment that public PyPI `api-utils` is unrelated).
- Every `src/routes/*_routes.py` imports its service from `src.services.*`. Zero `from api_utils.services import *Service` in `src/routes/` (filter/order constants from api_utils are allowed only if a factory needs them; prefer MRO lookup).
- Shared GET factories used where specified; aggregation composite and journey get-or-create stay local.
- `README.md` states the `api-utils==1.0.0` pin, that `src/services/` subclasses shared classes, and that routes import those subclasses (JSON-array list GETs, `offset`/`size` headers).
- Route unit tests keep patching `src.routes.<module>.<Service>.*`. Add tests for new GET list / journey by-id. Existing PATCH/POST tests still pass.
- E2E covers new GETs and existing control flows.

## Testing Expectations

Run all commands from this API repository root.

- **Install**
  - `mh` once per shell if CodeArtifact credentials are not already available
  - `pipenv run install`
  - Confirm `importlib.metadata.version("api-utils") == "1.0.0"`
- **Confirmation greps** (zero hits in `src/routes/`)
  - `rg "from api_utils.services import .+Service" src/routes`
  - `rg "from api_utils.services import JourneyService" src/`
- **Unit / lint / build**
  - `pipenv run test`
  - `pipenv run lint`
  - `pipenv run build`
- **Dev E2E**
  - `pipenv run db` if needed
  - `pipenv run dev` (separate terminal or background)
  - `pipenv run e2e`
- **Packaging verification**
  - `pipenv run container`
  - `pipenv run api`
  - `pipenv run e2e` against the containerized API
  - `curl -s http://localhost:8393/docs/openapi.yaml` — includes F203 GETs

## Outputs

- `Pipfile` — pin `api-utils==1.0.0`
- `Pipfile.lock` — refresh via `pipenv run install` (use `scripts/pipenv-lock.sh` if hashes must be regenerated first)
- `README.md` — 1.0.0 pin, local subclasses, list GET contract
- `src/routes/journey_routes.py`
- `src/routes/note_routes.py`
- `src/routes/aggregation_routes.py`
- `src/routes/event_routes.py`
- `src/routes/resource_routes.py`
- `src/routes/path_routes.py`
- `src/routes/__init__.py` — only if exports are needed
- `src/server.py` — only if blueprint constructors or log lines must change
- `test/routes/test_journey_routes.py`
- `test/routes/test_note_routes.py`
- `test/routes/test_aggregation_routes.py`
- `test/routes/test_event_routes.py`
- `test/routes/test_resource_routes.py`
- `test/routes/test_path_routes.py`
- `test/test_server.py` — only if URL-rule assertions need updates
- `test/e2e/test_note.py` — add list GET
- `test/e2e/test_event.py` — add list GET
- `test/e2e/test_journey.py` — add by-id GET if missing
- `test/e2e/e2e_auth.py` — only if `profile_id` is missing

The agent must not update files outside this list.

## Execution Notes

- Pinned `api-utils==1.0.0` in `Pipfile` and updated `Pipfile.lock` with `scripts/pipenv-lock.sh` and `pipenv run install`.
- Wired all route modules (`src/routes/*_routes.py`) to use shared GET route factories and local service subclasses under `src/services/`.
- Updated `README.md` to document the 1.0.0 pin and local service architecture.
- Updated route unit tests (`test/routes/*`) and added unit test coverage for new GET list / by-id routes.
- Updated and added E2E tests (`test/e2e/*`) for new GET endpoints.
- Verified complete QA gate: `pipenv run container`, `pipenv run api`, and `pipenv run e2e` (all 36 E2E tests passed).
