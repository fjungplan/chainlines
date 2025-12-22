import pytest
from app.models.sponsor import SponsorBrand

@pytest.mark.asyncio
async def test_sponsor_brand_protection_defaults():
    """Test that SponsorBrand has is_protected field defaulting to False."""
    brand = SponsorBrand(
        brand_name="Test Brand",
        default_hex_color="#FFFFFF"
        # is_protected should be available
    )
    
    assert hasattr(brand, "is_protected"), "SponsorBrand model missing is_protected field"
    assert brand.is_protected is False
    
    brand.is_protected = True
    assert brand.is_protected is True
