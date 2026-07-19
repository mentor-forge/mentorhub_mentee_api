# Extend Resource list filters in api-utils

**Status**: Resolved (upstream shipped)

## Summary

`mentorhub_mentee_api` needs `GET /api/resource` to accept additional list query filters so the mentee SPA can search by **url**, **interests**, **technologies**, and **skill_level** (in addition to existing `name`, `description`, and `status`).

List filter parsing and Mongo match building for resources live in **`api-utils`** (`RESOURCE_LIST_FILTERS` on `ResourceService`), not in the mentee API route.

## Upstream resolution

Shipped in `mentorhub_api_utils` (merged to `main`, package version **`0.5.1`**):

| Task | Result |
|------|--------|
| `SHIPPED.R056.extend_resource_list_filters.md` | Extended `RESOURCE_LIST_FILTERS` |
| `SHIPPED.R057.test_resource_list_multi_field_filters.md` | Unit tests for new filters |
| `SHIPPED.R058.bump_patch_resource_list_filters.md` | Version bump to `0.5.1` |

`README.md` documents pinned SemVer as `api-utils==0.5.1`. Shared Get List pattern is unchanged: per-service `*_LIST_FILTERS` specs with `contains` / `in_list` only — Resource’s multi-field map does not constrain other domains (e.g. Profiles).

Confirmed `RESOURCE_LIST_FILTERS` on `main`:

```python
RESOURCE_LIST_FILTERS = {
    "name": {"type": "contains", "field": "name"},
    "description": {"type": "contains", "field": "description"},
    "status": {"type": "in_list", "field": "status"},
    "url": {"type": "contains", "field": "url"},
    "interests": {"type": "in_list", "field": "interests"},
    "technologies": {"type": "in_list", "field": "technologies"},
    "skill_level": {"type": "in_list", "field": "skill_level"},
}
```

Multiple filters remain **AND**ed via `build_match_filter`. No new filter types and no global `q` / OR-across-fields search were added.

## Downstream (this repo)

- `PENDING.L190.bump_api_utils_resource_list_filters.md` — pin `api-utils==0.5.1`
- `PENDING.L191.document_resource_list_multi_field_filters.md` — OpenAPI + route docstring
- `PENDING.L192.test_resource_list_multi_field_filters.md` — route + E2E coverage
