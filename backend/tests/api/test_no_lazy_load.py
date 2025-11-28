import pytest


@pytest.mark.asyncio
async def test_team_history_no_lazy_load(test_client):
    # This relies on fixtures creating baseline data in SQLite.
    # Call an arbitrary history endpoint; should not raise MissingGreenlet.
    # Using a zero UUID should 404; then we create basic data in a separate test.
    resp = await test_client.get("/api/v1/teams/00000000-0000-0000-0000-000000000000/history")
    assert resp.status_code in (404, 200)


@pytest.mark.asyncio
async def test_timeline_no_lazy_load(test_client):
    # Ensure timeline endpoint returns successfully without async lazy-load errors.
    resp = await test_client.get("/api/v1/timeline?start_year=2000&end_year=2030&include_dissolved=true")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data and "links" in data