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
    """Test POST /api/event endpoint."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "type": "link",
        "context": {"profile_id": "507f1f77bcf86cd799439011"},
    }

    response = requests.post(f"{BASE_URL}/api/event", headers=headers, json=data)
    assert response.status_code == 201, _err(response, 201)

    response_data = response.json()
    assert "_id" in response_data, "Response missing '_id' key"
    assert response_data.get("type") == "link"
    assert "created" in response_data


@pytest.mark.e2e
def test_event_endpoint_requires_auth():
    """Test that event create requires authentication."""
    response = requests.post(f"{BASE_URL}/api/event", json={"type": "link"})
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
