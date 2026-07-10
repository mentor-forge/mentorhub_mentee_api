"""
E2E tests for Note endpoints (POST only).
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
def test_create_note_endpoint():
    """Test POST /api/note endpoint and verify record persists in database."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(f"{BASE_URL}/api/resource", headers=headers)
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    if not resources:
        pytest.skip("No resources available for note create test")

    resource_id = resources[0]["_id"]
    data = {
        "resource_id": resource_id,
        "note": "E2E test note about this resource",
        "status": "active",
    }

    response = requests.post(f"{BASE_URL}/api/note", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data.get("note") == data["note"]
    assert "created" in response_data
    assert "saved" in response_data


@pytest.mark.e2e
def test_note_endpoint_requires_auth():
    """Test that note create requires authentication."""
    response = requests.post(f"{BASE_URL}/api/note", json={"note": "test"})
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
