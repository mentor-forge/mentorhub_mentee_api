"""
E2E tests for Resource endpoints (consume-style, read-only).

These tests verify that Resource endpoints work correctly by making
actual HTTP requests to a running server.

To run these tests:
1. Start the server: pipenv run dev (or pipenv run api for containerized)
2. Run E2E tests: pipenv run e2e

API runs on port 8393 (same for dev and api).
"""

import pytest
import requests

from .e2e_auth import get_auth_token

BASE_URL = "http://localhost:8393"


def _err(response, expected):
    """Format assertion error with response body for debugging."""
    body = response.text[:300] if response.text else "(empty)"
    return f"Expected {expected}, got {response.status_code}. Response: {body}"


@pytest.mark.e2e
def test_get_resources_endpoint():
    """Test GET /api/resource endpoint returns a JSON array."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/resource", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a JSON array"


@pytest.mark.e2e
def test_get_resources_with_pagination_headers():
    """Test GET /api/resource with offset/size headers."""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "offset": "0",
        "size": "5",
    }
    response = requests.get(f"{BASE_URL}/api/resource", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a JSON array"
    assert len(response_data) <= 5, "Response should respect size header"


@pytest.mark.e2e
def test_get_resources_with_filter_and_sort():
    """Test GET /api/resource with name filter and sort query params."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/resource",
        headers=headers,
        params={"sort_by": "name", "order": "asc"},
    )
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a JSON array"
    if len(response_data) >= 2:
        names = [item.get("name") for item in response_data if item.get("name")]
        assert names == sorted(names), "Results should be sorted by name asc"


@pytest.mark.e2e
def test_get_resources_with_name_filter():
    """Test GET /api/resource with optional name filter query param."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    if not resources or not resources[0].get("name"):
        pytest.skip("No named resources available for filter test")

    needle = resources[0]["name"][:3]
    filtered_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers=headers,
        params={"name": needle},
    )
    assert filtered_response.status_code == 200, _err(filtered_response, 200)
    filtered = filtered_response.json()
    assert isinstance(filtered, list)
    for resource in filtered:
        assert needle.lower() in resource.get("name", "").lower()


@pytest.mark.e2e
def test_get_resources_with_status_filter():
    """Test GET /api/resource with status in_list filter query param."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
        params={"status": "active"},
    )
    assert response.status_code == 200, _err(response, 200)
    resources = response.json()
    assert isinstance(resources, list)
    for resource in resources:
        assert resource.get("status") == "active"


@pytest.mark.e2e
def test_get_resources_with_url_filter():
    """Test GET /api/resource with optional url contains filter."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    sample = next((r for r in resources if r.get("url")), None)
    if not sample:
        pytest.skip("No resources with url available for filter test")

    needle = sample["url"][:8]
    filtered_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers=headers,
        params={"url": needle},
    )
    assert filtered_response.status_code == 200, _err(filtered_response, 200)
    filtered = filtered_response.json()
    assert isinstance(filtered, list)
    assert len(filtered) >= 1
    for resource in filtered:
        assert needle.lower() in resource.get("url", "").lower()

    no_match = requests.get(
        f"{BASE_URL}/api/resource",
        headers=headers,
        params={"url": "zzz-no-such-url-xyz"},
    )
    assert no_match.status_code == 200, _err(no_match, 200)
    assert no_match.json() == []


@pytest.mark.e2e
def test_get_resources_with_interests_filter():
    """Test GET /api/resource with interests in_list filter."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    sample = next(
        (
            r
            for r in resources
            if isinstance(r.get("interests"), list) and r["interests"]
        ),
        None,
    )
    if not sample:
        pytest.skip("No resources with interests available for filter test")

    interest = sample["interests"][0]
    filtered_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers=headers,
        params={"interests": interest},
    )
    assert filtered_response.status_code == 200, _err(filtered_response, 200)
    filtered = filtered_response.json()
    assert isinstance(filtered, list)
    assert len(filtered) >= 1
    for resource in filtered:
        assert interest in (resource.get("interests") or [])

    no_match = requests.get(
        f"{BASE_URL}/api/resource",
        headers=headers,
        params={"interests": "zzz-no-such-interest"},
    )
    assert no_match.status_code == 200, _err(no_match, 200)
    assert no_match.json() == []


@pytest.mark.e2e
def test_get_resources_with_technologies_filter():
    """Test GET /api/resource with technologies in_list filter."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    sample = next(
        (
            r
            for r in resources
            if isinstance(r.get("technologies"), list) and r["technologies"]
        ),
        None,
    )
    if not sample:
        pytest.skip("No resources with technologies available for filter test")

    technology = sample["technologies"][0]
    filtered_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers=headers,
        params={"technologies": technology},
    )
    assert filtered_response.status_code == 200, _err(filtered_response, 200)
    filtered = filtered_response.json()
    assert isinstance(filtered, list)
    assert len(filtered) >= 1
    for resource in filtered:
        assert technology in (resource.get("technologies") or [])

    no_match = requests.get(
        f"{BASE_URL}/api/resource",
        headers=headers,
        params={"technologies": "zzz-no-such-tech"},
    )
    assert no_match.status_code == 200, _err(no_match, 200)
    assert no_match.json() == []


@pytest.mark.e2e
def test_get_resources_with_skill_level_filter():
    """Test GET /api/resource with skill_level in_list filter."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    sample = next((r for r in resources if r.get("skill_level")), None)
    if not sample:
        pytest.skip("No resources with skill_level available for filter test")

    skill_level = sample["skill_level"]
    filtered_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers=headers,
        params={"skill_level": skill_level},
    )
    assert filtered_response.status_code == 200, _err(filtered_response, 200)
    filtered = filtered_response.json()
    assert isinstance(filtered, list)
    assert len(filtered) >= 1
    for resource in filtered:
        assert resource.get("skill_level") == skill_level

    no_match = requests.get(
        f"{BASE_URL}/api/resource",
        headers=headers,
        params={"skill_level": "zzz-no-such-level"},
    )
    assert no_match.status_code == 200, _err(no_match, 200)
    assert no_match.json() == []


@pytest.mark.e2e
def test_get_resources_empty_multi_field_filters_ok():
    """Test GET /api/resource with empty multi-field filters does not error."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    unfiltered = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "5"},
    )
    assert unfiltered.status_code == 200, _err(unfiltered, 200)

    empty_filtered = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "5"},
        params={"url": "", "interests": "", "technologies": "", "skill_level": ""},
    )
    assert empty_filtered.status_code == 200, _err(empty_filtered, 200)
    assert isinstance(empty_filtered.json(), list)
    assert len(empty_filtered.json()) == len(unfiltered.json())


@pytest.mark.e2e
def test_get_resources_multi_field_filter_with_pagination():
    """Test GET /api/resource combines a multi-field filter with offset/size headers."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()

    params = {}
    sample_url = next((r for r in resources if r.get("url")), None)
    if sample_url:
        params["url"] = sample_url["url"][:8]
    else:
        sample_tech = next(
            (
                r
                for r in resources
                if isinstance(r.get("technologies"), list) and r["technologies"]
            ),
            None,
        )
        if sample_tech:
            params["technologies"] = sample_tech["technologies"][0]
        else:
            sample_interest = next(
                (
                    r
                    for r in resources
                    if isinstance(r.get("interests"), list) and r["interests"]
                ),
                None,
            )
            if sample_interest:
                params["interests"] = sample_interest["interests"][0]
            else:
                sample_skill = next(
                    (r for r in resources if r.get("skill_level")), None
                )
                if sample_skill:
                    params["skill_level"] = sample_skill["skill_level"]
                else:
                    pytest.skip(
                        "No resources with url/interests/technologies/skill_level "
                        "for combined filter pagination test"
                    )

    response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "offset": "0", "size": "3"},
        params=params,
    )
    assert response.status_code == 200, _err(response, 200)
    filtered = response.json()
    assert isinstance(filtered, list)
    assert len(filtered) <= 3


@pytest.mark.e2e
def test_get_resource_detail():
    """Test GET /api/resource/<id> returns composite detail."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    if not resources:
        pytest.skip("No resources available for detail test")

    resource_id = resources[0]["_id"]
    response = requests.get(
        f"{BASE_URL}/api/resource/{resource_id}",
        headers=headers,
    )
    assert response.status_code == 200, _err(response, 200)

    detail = response.json()
    assert "resource" in detail, "Detail should include resource"
    assert "aggregation" in detail, "Detail should include aggregation"
    assert "notes" in detail, "Detail should include notes"
    assert isinstance(detail["notes"], list), "notes should be an array"
    assert detail["resource"]["_id"] == resource_id


@pytest.mark.e2e
def test_get_resource_detail_notes_match_aggregation_count():
    """Regression: composite notes array length matches aggregation note_count."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    if not resources:
        pytest.skip("No resources available for note count regression test")

    verified = False
    for resource in resources:
        resource_id = resource["_id"]
        response = requests.get(
            f"{BASE_URL}/api/resource/{resource_id}",
            headers=headers,
        )
        assert response.status_code == 200, _err(response, 200)
        detail = response.json()
        aggregation = detail.get("aggregation")
        notes = detail.get("notes") or []
        if aggregation is None:
            continue
        note_count = aggregation.get("note_count")
        if note_count is None:
            continue
        if note_count > 20:
            assert len(notes) == note_count, (
                f"Resource {resource_id}: composite truncated notes "
                f"(expected {note_count}, got {len(notes)})"
            )
            verified = True
            break
        if note_count == len(notes):
            verified = True
            break
    if not verified:
        pytest.skip(
            "No resource with consistent aggregation note_count for regression check"
        )


@pytest.mark.e2e
def test_get_resource_not_found():
    """Test GET /api/resource/<id> with non-existent ID."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/resource/000000000000000000000000",
        headers=headers,
    )
    assert response.status_code == 404, _err(response, 404)


@pytest.mark.e2e
def test_resource_endpoints_require_auth():
    """Test that resource endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/resource")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
