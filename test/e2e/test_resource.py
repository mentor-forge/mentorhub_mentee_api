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
def test_get_resource_detail():
    """Test GET /api/resource/<id> returns composite detail."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(f"{BASE_URL}/api/resource", headers=headers)
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
