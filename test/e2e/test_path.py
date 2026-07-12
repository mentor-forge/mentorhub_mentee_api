"""
E2E tests for Path endpoints (consume-style, read-only).

These tests verify that Path endpoints work correctly by making
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
def test_get_paths_endpoint():
    """Test GET /api/path returns a paginated JSON array."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/path", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a JSON array"


@pytest.mark.e2e
def test_get_paths_with_pagination_headers():
    """Test GET /api/path with offset/size headers."""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "offset": "0",
        "size": "5",
    }
    response = requests.get(f"{BASE_URL}/api/path", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, list), "Response should be a JSON array"
    assert len(response_data) <= 5, "Response should respect size header"


@pytest.mark.e2e
def test_get_paths_with_name_filter():
    """Test GET /api/path with optional name filter query param."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/path",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    paths = list_response.json()
    if not paths or not paths[0].get("name"):
        pytest.skip("No named paths available for filter test")

    needle = paths[0]["name"][:3]
    filtered_response = requests.get(
        f"{BASE_URL}/api/path",
        headers={**headers, "size": "100"},
        params={"name": needle},
    )
    assert filtered_response.status_code == 200, _err(filtered_response, 200)
    filtered = filtered_response.json()
    for path in filtered:
        assert needle.lower() in path.get("name", "").lower()


@pytest.mark.e2e
def test_get_path_detail_enriched_resources():
    """Test GET /api/path/<id> returns enriched resource summaries."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/path",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)

    paths = list_response.json()
    if not paths:
        pytest.skip("No Path documents in test data")

    path_id = paths[0]["_id"]
    detail_response = requests.get(
        f"{BASE_URL}/api/path/{path_id}",
        headers=headers,
    )
    assert detail_response.status_code == 200, _err(detail_response, 200)

    path = detail_response.json()
    modules = path.get("modules") or []
    for module in modules:
        for topic in module.get("topics") or []:
            for resource in topic.get("resources") or []:
                if isinstance(resource, dict):
                    assert "_id" in resource
                    if resource.get("name") is not None:
                        assert "name" in resource
                    if resource.get("description") is not None:
                        assert "description" in resource


@pytest.mark.e2e
def test_get_path_not_found():
    """Test GET /api/path/<id> with non-existent ID."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/path/000000000000000000000000",
        headers=headers,
    )
    assert response.status_code == 404, _err(response, 404)


@pytest.mark.e2e
def test_path_endpoints_require_auth():
    """Test that path endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/path")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
