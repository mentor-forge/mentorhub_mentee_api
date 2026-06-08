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
    """Test GET /api/resource endpoint."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/resource", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert "limit" in response_data, "Response should have 'limit' key"
    assert "has_more" in response_data, "Response should have 'has_more' key"
    assert "next_cursor" in response_data, "Response should have 'next_cursor' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


@pytest.mark.e2e
def test_get_resources_with_name_filter():
    """Test GET /api/resource with name query parameter."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/resource?name=test", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    response_data = response.json()
    assert isinstance(response_data, dict), "Response should be a dict (infinite scroll format)"
    assert "items" in response_data, "Response should have 'items' key"
    assert isinstance(response_data["items"], list), "Items should be a list"


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
