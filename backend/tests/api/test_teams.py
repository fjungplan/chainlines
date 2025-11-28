import uuid
import pytest


@pytest.mark.asyncio
async def test_get_team_by_id_success(test_client, isolated_session, sample_team_node, sample_team_era):
    # Fetch the node via API
    resp = await test_client.get(f"/api/v1/teams/{sample_team_node.node_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["node_id"] == str(sample_team_node.node_id)
    assert data["founding_year"] == sample_team_node.founding_year
    # Should include eras list with at least one item
    assert isinstance(data.get("eras"), list)
    assert any(e["era_id"] == str(sample_team_era.era_id) for e in data["eras"]) is True


@pytest.mark.asyncio
async def test_get_team_by_id_not_found(test_client):
    missing_id = uuid.uuid4()
    resp = await test_client.get(f"/api/v1/teams/{missing_id}")
    assert resp.status_code == 404
    body = resp.json()
    # Our domain exception format: top-level detail and code
    assert body.get("code") == "node_not_found"
    assert "not found" in body.get("detail", "").lower()


@pytest.mark.asyncio
async def test_get_team_eras_list_and_filter(test_client, isolated_session, sample_team_node):
    # Create multiple eras
    from app.models.team import TeamEra

    e1 = TeamEra(node_id=sample_team_node.node_id, season_year=2020, registered_name="A", tier_level=1)
    e2 = TeamEra(node_id=sample_team_node.node_id, season_year=2021, registered_name="B", tier_level=1)
    await isolated_session.merge(e1)
    await isolated_session.merge(e2)
    await isolated_session.commit()

    # List all
    resp = await test_client.get(f"/api/v1/teams/{sample_team_node.node_id}/eras")
    assert resp.status_code == 200
    eras = resp.json()
    assert [e["season_year"] for e in eras] == [2021, 2020]  # desc order

    # Filter by year
    resp = await test_client.get(f"/api/v1/teams/{sample_team_node.node_id}/eras", params={"year": 2020})
    assert resp.status_code == 200
    eras = resp.json()
    assert len(eras) == 1 and eras[0]["season_year"] == 2020


@pytest.mark.asyncio
async def test_list_teams_pagination_and_filters(test_client, sample_teams_in_db):
    # Pagination
    resp = await test_client.get("/api/v1/teams", params={"skip": 0, "limit": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 2
    assert data["skip"] == 0
    assert data["total"] >= 5
    assert len(data["items"]) <= 2

    # Filter by active_in_year (choose a year known from fixture, e.g., 2021)
    resp = await test_client.get("/api/v1/teams", params={"active_in_year": 2021})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1

    # Filter by tier_level (1-3)
    resp = await test_client.get("/api/v1/teams", params={"tier_level": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
