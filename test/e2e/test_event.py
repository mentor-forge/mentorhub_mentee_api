"""
E2E tests for Event endpoints (POST only).
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
def test_create_event_endpoint():
    """Test POST /api/event endpoint with type-only body and token-sourced context."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {"type": "link"}

    response = requests.post(f"{BASE_URL}/api/event", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data.get("type") == "link"
    assert "created" in response_data

    context = response_data.get("context", {})
    assert context.get("user_id") == "mike"
    assert context.get("name") == "Mike Storey"
    assert context.get("roles") == ["admin"]
    assert context.get("profile_id", "").lower() == "a00000000000000000000001"
    assert context.get("customer_id") == "D00000000000000000000006"
    assert context.get("mentor_id") == ""
    assert "remote_ip" in context


@pytest.mark.e2e
def test_create_event_ignores_client_context():
    """Client-supplied context must not override token-sourced context."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "type": "login",
        "context": {"profile_id": "507f1f77bcf86cd799439099"},
    }

    response = requests.post(f"{BASE_URL}/api/event", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    context = response.json().get("context", {})
    assert context.get("profile_id", "").lower() == "a00000000000000000000001"
    assert context.get("profile_id", "").lower() != "507f1f77bcf86cd799439099"


@pytest.mark.e2e
def test_event_endpoint_requires_auth():
    """Test that event create requires authentication."""
    response = requests.post(f"{BASE_URL}/api/event", json={"type": "link"})
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
