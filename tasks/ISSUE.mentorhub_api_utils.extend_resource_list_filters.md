# Extend Resource list filters in api-utils

## Summary

`mentorhub_mentee_api` needs `GET /api/resource` to accept additional list query filters so the mentee SPA can search by **url**, **interests**, **technologies**, and **skill_level** (in addition to existing `name`, `description`, and `status`).

List filter parsing and Mongo match building for resources live in **`api-utils`** (`RESOURCE_LIST_FILTERS` on `ResourceService`), not in the mentee API route. Extend and publish api-utils first; mentee API then bumps the pin and documents/tests the contract.

Do **not** implement this from mentee API orchestration — plan and ship in `mentorhub_api_utils`, then unblock mentee API tasks `L190`–`L192`.

## Current contract (`api-utils` 0.5.0)

`RESOURCE_LIST_FILTERS` in `api_utils/services/resource_service.py`:

| Query param | Type | Behavior |
|-------------|------|----------|
| `name` | `contains` | Case-insensitive substring on `name` |
| `description` | `contains` | Case-insensitive substring on `description` |
| `status` | `in_list` | Comma-separated values → field `$in` |

`build_match_filter` already ANDs all provided filters into the match document (preferred; matches today’s composition).

## Requested api-utils changes

Extend `RESOURCE_LIST_FILTERS` (and any related unit tests) consistently with existing patterns:

| Query param | Suggested type | Match behavior |
|-------------|----------------|----------------|
| `url` | `contains` | Case-insensitive substring on `url` |
| `interests` | `in_list` | Comma-separated values; Mongo `$in` on `interests` (array field — matches if any element is in the list) |
| `technologies` | `in_list` | Comma-separated values; Mongo `$in` on `technologies` |
| `skill_level` | `in_list` | Comma-separated values; Mongo `$in` on scalar `skill_level` |

Also:

1. Keep `name` / `description` / `status` / order / pagination behavior unchanged.
2. Confirm multiple filters remain **AND**ed (no OR-across-fields / single `q` param).
3. Add unit tests in api-utils covering each new filter (empty omitted, match, no-match, combined).
4. Bump and publish a new `api-utils` version to CodeArtifact (suggest patch `0.5.1` unless a larger release is already in flight).

## Notes

- Field name is **`technologies`** (plural), not `technology`.
- Field name is **`skill_level`**.
- Existing `contains` / `in_list` types in `list_query.py` should be sufficient — no new filter type required for array `$in` semantics.
- Out of scope: Resource document shape, enumerator values, mentee OpenAPI/docs (owned by mentee API after the bump), SPA UI.

## Downstream (after publish)

Mentee API tasks (this repo):

- `PENDING.L190.bump_api_utils_resource_list_filters.md` — pin and install the published version
- `PENDING.L191.document_resource_list_multi_field_filters.md` — OpenAPI + route docstring
- `PENDING.L192.test_resource_list_multi_field_filters.md` — route + E2E coverage
