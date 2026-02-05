import pytest
from httpx import AsyncClient

@pytest.fixture
async def admin_client(client: AsyncClient, admin_user_token: str):
    """Authenticated client for admin."""
    client.headers["Authorization"] = f"Bearer {admin_user_token}"
    return client


@pytest.mark.asyncio
async def test_get_families_list(admin_client: AsyncClient, isolated_session):
    """Test GET /admin/optimizer/families"""
    # Create a precomputed layout entry for testing
    from app.models.precomputed_layout import PrecomputedLayout
    from app.optimizer.fingerprint_service import compute_family_hash
    import uuid
    from datetime import datetime

    fingerprint = {
        "node_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
        "link_ids": [str(uuid.uuid4())],
        "node_years": {},
        "link_years": {}
    }
    family_hash = compute_family_hash(fingerprint)
    
    layout = PrecomputedLayout(
        family_hash=family_hash,
        layout_data={"chains": [{"id": "c1"}, {"id": "c2"}], "links": [{"id": "l1"}]},
        data_fingerprint=fingerprint,
        score=123.45,
        optimized_at=datetime.now()
    )
    isolated_session.add(layout)
    await isolated_session.commit()

    response = await admin_client.get("/api/v1/admin/optimizer/families")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = next((i for i in data if i["family_hash"] == family_hash), None)
    assert item is not None
    assert item["score"] == 123.45


@pytest.mark.asyncio
async def test_trigger_optimization(admin_client: AsyncClient, isolated_session):
    """Test POST /admin/optimizer/optimize"""
    # Create a layout to optimize
    from app.models.precomputed_layout import PrecomputedLayout
    from app.optimizer.fingerprint_service import compute_family_hash
    import uuid
    
    fingerprint = {
        "node_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
        "link_ids": [str(uuid.uuid4())],
        "node_years": {},
        "link_years": {}
    }
    family_hash = compute_family_hash(fingerprint)
    
    layout = PrecomputedLayout(
        family_hash=family_hash,
        layout_data={"chains": []},
        data_fingerprint=fingerprint,
        score=100.0
    )
    isolated_session.add(layout)
    await isolated_session.commit()

    payload = {
        "family_hashes": [family_hash]
    }
    
    response = await admin_client.post("/api/v1/admin/optimizer/optimize", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["message"] == "Optimization started"
    assert data["task_id"] is not None


@pytest.mark.asyncio
async def test_get_status(admin_client: AsyncClient):
    """Test GET /admin/optimizer/status"""
    response = await admin_client.get("/api/v1/admin/optimizer/status")
    assert response.status_code == 200
    data = response.json()
    assert "active_tasks" in data


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Verify 403/401 for non-admin"""
    # Assuming client is unauthenticated or regular user
    response = await client.get("/api/v1/admin/optimizer/families")
    # Should be 401 (Unauthenticated) or 403 (Forbidden)
    assert response.status_code in [401, 403]
