"""
Tests for the Public Precomputed Layouts API.
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_all_layouts(client: AsyncClient, isolated_session):
    """Test GET /api/v1/precomputed-layouts"""
    from app.models.precomputed_layout import PrecomputedLayout
    from app.optimizer.fingerprint_service import compute_family_hash
    import uuid
    from datetime import datetime

    fingerprint = {
        "node_ids": [str(uuid.uuid4())],
        "link_ids": [],
        "node_years": {},
        "link_years": {}
    }
    family_hash = compute_family_hash(fingerprint)
    
    layout = PrecomputedLayout(
        family_hash=family_hash,
        layout_data={"chains": ["some_data"]},
        data_fingerprint=fingerprint,
        score=99.9,
        optimized_at=datetime.now()
    )
    isolated_session.add(layout)
    await isolated_session.commit()

    response = await client.get("/api/v1/precomputed-layouts")
    assert response.status_code == 200
    data = response.json()
    
    assert family_hash in data
    assert data[family_hash]["score"] == 99.9
    assert data[family_hash]["layout_data"]["chains"] == ["some_data"]
