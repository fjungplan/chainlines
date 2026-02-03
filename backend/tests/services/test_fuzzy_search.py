import pytest
import uuid
from sqlalchemy import text
from app.services.sponsor_service import SponsorService
from app.models.sponsor import SponsorMaster, SponsorBrand

@pytest.mark.asyncio
async def test_search_brands_fuzzy(db_session):
    # 1. Setup Data: Create a brand with accent "Citroën"
    master = SponsorMaster(
        master_id=uuid.uuid4(),
        legal_name="Citroen Group",
        industry_sector="Automotive"
    )
    db_session.add(master)
    
    brand = SponsorBrand(
        brand_id=uuid.uuid4(),
        master_id=master.master_id,
        brand_name="Citroën",
        default_hex_color="#ff0000"
    )
    db_session.add(brand)
    await db_session.commit()

    # 2. Search using unaccented term "Citroen"
    # This should find "Citroën" if unaccent logic is working
    results = await SponsorService.search_brands(db_session, "Citroen")
    
    # 3. Verify
    assert len(results) > 0
    assert results[0].brand_name == "Citroën"

@pytest.mark.asyncio
async def test_search_masters_fuzzy(db_session):
    # 1. Setup Data: Create specific accented master
    master = SponsorMaster(
        master_id=uuid.uuid4(),
        legal_name="Crédit Agricole",
        industry_sector="Banking"
    )
    db_session.add(master)
    await db_session.commit()

    # 2. Search unaccented "Credit"
    results = await SponsorService.search_masters(db_session, "Credit")
    
    assert len(results) > 0
    assert results[0].legal_name == "Crédit Agricole"
