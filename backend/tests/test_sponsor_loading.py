import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.team import TeamNode, TeamEra
from app.services.sponsor_service import SponsorService
from app.schemas.sponsors import SponsorMasterCreate, SponsorBrandCreate
from datetime import date

@pytest.mark.asyncio
async def test_get_era_sponsor_links_eager_loading(db_session: AsyncSession):
    """
    Verify that get_era_sponsor_links eager loads the brand relationship.
    This is critical for the frontend to display brand names and colors.
    """
    # 1. Setup Data
    node = TeamNode(founding_year=2024, legal_name="Loading Test Node")
    db_session.add(node)
    await db_session.flush()

    era = TeamEra(
        node_id=node.node_id,
        season_year=2024,
        valid_from=date(2024, 1, 1),
        registered_name="Loading Team"
    )
    db_session.add(era)
    await db_session.flush()

    master = await SponsorService.create_master(
        db_session, 
        data=SponsorMasterCreate(legal_name="Loading Master"),
        user_id=None
    )
    brand = await SponsorService.add_brand(
        db_session,
        master.master_id,
        data=SponsorBrandCreate(brand_name="Loading Brand", default_hex_color="#FF00FF"),
        user_id=None
    )
    await db_session.commit()

    # 2. Create Link
    await SponsorService.link_sponsor_to_era(
        db_session,
        era.era_id,
        brand.brand_id,
        rank_order=1,
        prominence_percent=100,
        user_id=None
    )
    # Commit to ensure separate transaction/session state if needed, though we use same session here
    await db_session.commit()

    # 3. Fetch Links using the Service Method under test
    links = await SponsorService.get_era_sponsor_links(db_session, era.era_id)
    
    # 4. Assertions
    assert len(links) == 1
    link = links[0]
    
    # CRITICAL: Verify brand is loaded and accessible
    # Without eager loading, access to link.brand might invoke lazy load (if session open) 
    # or return None/Error depending on config.
    # explicit check:
    assert link.brand is not None, "Brand relationship should be loaded"
    assert link.brand.brand_name == "Loading Brand", "Brand name should be accessible"
    assert link.brand.default_hex_color == "#FF00FF", "Brand color should be accessible"
