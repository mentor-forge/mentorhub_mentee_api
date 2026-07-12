"""
E2E tests for Journey endpoints.
"""

import pytest
import requests

from .e2e_auth import get_auth_token

BASE_URL = "http://localhost:8393"


def _err(response, expected):
    body = response.text[:300] if response.text else "(empty)"
    return f"Expected {expected}, got {response.status_code}. Response: {body}"


@pytest.mark.e2e
def test_get_my_journey_endpoint():
    """GET /api/journey returns the token owner's journey document."""
    token = get_auth_token(profile_id="e00000000000000000000001")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_URL}/api/journey", headers=headers)
    assert response.status_code == 200, _err(response, 200)

    data = response.json()
    assert data["_id"] == "e00000000000000000000001"
    assert data.get("profile_id") == "e00000000000000000000001"
    assert "created" in data
    assert "saved" in data
    assert "library" in data
    assert "now" in data
    assert "next" in data


@pytest.mark.e2e
def test_get_my_journey_idempotent():
    """Repeated GET /api/journey returns the same journey _id."""
    profile_id = "e00000000000000000000002"
    token = get_auth_token(profile_id=profile_id)
    headers = {"Authorization": f"Bearer {token}"}

    first = requests.get(f"{BASE_URL}/api/journey", headers=headers)
    second = requests.get(f"{BASE_URL}/api/journey", headers=headers)

    assert first.status_code == 200, _err(first, 200)
    assert second.status_code == 200, _err(second, 200)
    assert first.json()["_id"] == second.json()["_id"] == profile_id


@pytest.mark.e2e
def test_journey_endpoints_require_auth():
    """Journey endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/journey")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
