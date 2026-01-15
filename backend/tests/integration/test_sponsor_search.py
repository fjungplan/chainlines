"""Integration tests for enhanced sponsor search functionality.

These tests verify that sponsor search:
1. Searches across sponsor master names AND brand names
2. Is accent-insensitive (e.g., "Cervelo" finds "Cervélo")
3. Returns deduplicated results
"""
import pytest
from app.services.sponsor_service import SponsorService
from app.models.sponsor import SponsorMaster, SponsorBrand


@pytest.mark.asyncio
async def test_search_by_sponsor_name(isolated_session):
    """
    Verify searching by sponsor master name returns the sponsor.
    """
    # Setup
    sponsor = SponsorMaster(legal_name="Mapei Sport")
    isolated_session.add(sponsor)
    await isolated_session.commit()
    
    # Action
    results = await SponsorService.search_masters(isolated_session, "Mapei", limit=10)
    
    # Assert
    assert len(results) == 1
    assert results[0].legal_name == "Mapei Sport"


@pytest.mark.asyncio
async def test_search_by_brand_name(isolated_session):
    """
    Verify searching by brand name returns the parent sponsor master.
    """
    # Setup
    sponsor = SponsorMaster(legal_name="Mapei Sport")
    isolated_session.add(sponsor)
    await isolated_session.flush()
    
    brand = SponsorBrand(
        master_id=sponsor.master_id,
        brand_name="Mapei Quick-Step",
        default_hex_color="#ff0000"
    )
    isolated_session.add(brand)
    await isolated_session.commit()
    
    # Action - search for brand name, not sponsor name
    results = await SponsorService.search_masters(isolated_session, "Quick-Step", limit=10)
    
    # Assert - should find the parent sponsor
    assert len(results) == 1
    assert results[0].legal_name == "Mapei Sport"


@pytest.mark.asyncio
async def test_search_accent_insensitive(isolated_session):
    """
    Verify search is accent-insensitive.
    
    Searching for "Cervelo" (no accent) should find "Cervélo" (with accent).
    """
    # Setup
    sponsor = SponsorMaster(legal_name="Cervélo Cycles")
    isolated_session.add(sponsor)
    await isolated_session.commit()
    
    # Action - search without accent
    results = await SponsorService.search_masters(isolated_session, "Cervelo", limit=10)
    
    # Assert - should find the sponsor with accent
    assert len(results) == 1
    assert results[0].legal_name == "Cervélo Cycles"


@pytest.mark.asyncio
async def test_search_brand_accent_insensitive(isolated_session):
    """
    Verify brand name search is also accent-insensitive.
    """
    # Setup
    sponsor = SponsorMaster(legal_name="Sponsor Company")
    isolated_session.add(sponsor)
    await isolated_session.flush()
    
    brand = SponsorBrand(
        master_id=sponsor.master_id,
        brand_name="Café de Colombia",
        default_hex_color="#00ff00"
    )
    isolated_session.add(brand)
    await isolated_session.commit()
    
    # Action - search without accent
    results = await SponsorService.search_masters(isolated_session, "Cafe de Colombia", limit=10)
    
    # Assert
    assert len(results) == 1
    assert results[0].legal_name == "Sponsor Company"


@pytest.mark.asyncio
async def test_search_no_duplicates(isolated_session):
    """
    Verify that when multiple brands match, the sponsor is only returned once.
    """
    # Setup
    sponsor = SponsorMaster(legal_name="Festina Watches")
    isolated_session.add(sponsor)
    await isolated_session.flush()
    
    brand1 = SponsorBrand(
        master_id=sponsor.master_id,
        brand_name="Festina",
        default_hex_color="#ff0000"
    )
    brand2 = SponsorBrand(
        master_id=sponsor.master_id,
        brand_name="Festina Lotus",
        default_hex_color="#00ff00"
    )
    isolated_session.add_all([brand1, brand2])
    await isolated_session.commit()
    
    # Action - search term matches both brands
    results = await SponsorService.search_masters(isolated_session, "Festina", limit=10)
    
    # Assert - should only return sponsor once, not twice
    assert len(results) == 1
    assert results[0].legal_name == "Festina Watches"


@pytest.mark.asyncio
async def test_search_multiple_sponsors(isolated_session):
    """
    Verify search returns multiple sponsors when appropriate.
    """
    # Setup
    sponsor1 = SponsorMaster(legal_name="Rabobank")
    sponsor2 = SponsorMaster(legal_name="Rabobank Nederland")
    isolated_session.add_all([sponsor1, sponsor2])
    await isolated_session.commit()
    
    # Action
    results = await SponsorService.search_masters(isolated_session, "Rabobank", limit=10)
    
    # Assert
    assert len(results) == 2
    names = {r.legal_name for r in results}
    assert "Rabobank" in names
    assert "Rabobank Nederland" in names
