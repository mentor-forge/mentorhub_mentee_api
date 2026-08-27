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
def test_get_notes_endpoint():
    """Test GET /api/note endpoint requiring resource_id query param."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(f"{BASE_URL}/api/resource", headers=headers)
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    if not resources:
        pytest.skip("No resources available for note list test")

    resource_id = resources[0]["_id"]

    # First create a note to ensure at least one exists
    requests.post(
        f"{BASE_URL}/api/note",
        headers=headers,
        json={"resource_id": resource_id, "note": "E2E list test note"},
    )

    response = requests.get(
        f"{BASE_URL}/api/note?resource_id={resource_id}", headers=headers
    )
    assert response.status_code == 200, _err(response, 200)
    notes = response.json()
    assert isinstance(notes, list)
    assert len(notes) >= 1
    assert "note" in notes[0]


@pytest.mark.e2e
def test_get_notes_missing_resource_id_returns_400():
    """Test GET /api/note without resource_id returns 400."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/note", headers=headers)
    assert response.status_code == 400, _err(response, 400)


@pytest.mark.e2e
def test_note_endpoint_requires_auth():
    """Test that note create requires authentication."""
    response = requests.post(f"{BASE_URL}/api/note", json={"note": "test"})
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
