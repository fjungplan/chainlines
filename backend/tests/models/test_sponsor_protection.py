import pytest
from app.models.sponsor import SponsorBrand, SponsorMaster

@pytest.mark.asyncio
async def test_sponsor_brand_protection_defaults(db_session):
    """Test that SponsorBrand has is_protected field defaulting to False."""
    master = SponsorMaster(legal_name="Test Master")
    db_session.add(master)
    await db_session.flush()

    brand = SponsorBrand(
        brand_name="Test Brand",
        default_hex_color="#FFFFFF",
        master_id=master.master_id
    )
    db_session.add(brand)
    await db_session.commit()
    await db_session.refresh(brand)

    assert hasattr(brand, "is_protected"), "SponsorBrand model missing is_protected field"
    assert brand.is_protected is False

    brand.is_protected = True
    assert brand.is_protected is True
