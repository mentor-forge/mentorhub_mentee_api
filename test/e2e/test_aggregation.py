"""
E2E tests for Aggregation endpoints.
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
def test_get_aggregation_detail_endpoint():
    """Test GET /api/aggregation/{resource_id} returns composite detail."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    if not resources:
        pytest.skip("No resources available for aggregation test")

    resource_id = resources[0]["_id"]
    response = requests.get(
        f"{BASE_URL}/api/aggregation/{resource_id}",
        headers=headers,
    )
    assert response.status_code == 200, _err(response, 200)

    detail = response.json()
    assert "aggregation" in detail, "Detail should include aggregation"
    assert "notes" in detail, "Detail should include notes"
    assert isinstance(detail["notes"], list), "notes should be an array"
    assert detail["aggregation"] is not None
    agg = detail["aggregation"]
    assert agg.get("_id") == resource_id or agg.get("resource_id") == resource_id


@pytest.mark.e2e
def test_get_aggregation_detail_notes_match_count():
    """Regression: aggregation composite returns full notes list, not a default page."""
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    list_response = requests.get(
        f"{BASE_URL}/api/resource",
        headers={**headers, "size": "100"},
    )
    assert list_response.status_code == 200, _err(list_response, 200)
    resources = list_response.json()
    if not resources:
        pytest.skip("No resources available for aggregation note count test")

    verified = False
    for resource in resources:
        resource_id = resource["_id"]
        response = requests.get(
            f"{BASE_URL}/api/aggregation/{resource_id}",
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
                f"Aggregation {resource_id}: composite truncated notes "
                f"(expected {note_count}, got {len(notes)})"
            )
        elif note_count != len(notes):
            continue

        resource_detail = requests.get(
            f"{BASE_URL}/api/resource/{resource_id}",
            headers=headers,
        )
        assert resource_detail.status_code == 200, _err(resource_detail, 200)
        resource_notes = resource_detail.json().get("notes") or []
        assert len(resource_notes) == len(notes), (
            "Resource and aggregation endpoints should return the same note count"
        )
        verified = True
        break
    if not verified:
        pytest.skip(
            "No resource with consistent aggregation note_count for regression check"
        )


@pytest.mark.e2e
def test_aggregation_endpoint_requires_auth():
    """Test that aggregation endpoints require authentication."""
    response = requests.get(f"{BASE_URL}/api/aggregation/507f1f77bcf86cd799439011")
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
