import pytest
from datetime import date
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.sponsor import SponsorMaster, SponsorBrand, TeamSponsorLink
from app.models.team import TeamNode, TeamEra
from app.services.sponsor_service import SponsorService

@pytest.mark.asyncio
async def test_merge_brands_standard(db_session: AsyncSession):
    """
    Test Case 1: Standard Brand A -> Brand B merge.
    All links should transfer to B, and A should be deleted.
    """
    # 1. Setup Data
    master = SponsorMaster(legal_name="Merge Test 1")
    db_session.add(master)
    await db_session.flush()

    brand_a = SponsorBrand(master_id=master.master_id, brand_name="Brand A", default_hex_color="#000000")
    brand_b = SponsorBrand(master_id=master.master_id, brand_name="Brand B", default_hex_color="#FFFFFF")
    db_session.add(brand_a)
    db_session.add(brand_b)
    await db_session.flush()

    # Create dummy parent node for eras
    node = TeamNode(legal_name="Merge Node 1", founding_year=1990)
    db_session.add(node)
    await db_session.flush()

    # Create dummy eras and links for Brand A
    eras = []
    for i in range(5):
        era = TeamEra(
            node_id=node.node_id,
            registered_name=f"Era {i}", 
            season_year=2000+i, 
            valid_from=date(2000+i, 1, 1),
            uci_code=f"E0{i}",
            country_code="ITA"
        )
        db_session.add(era)
        eras.append(era)
    await db_session.flush()

    for i, era in enumerate(eras):
        link = TeamSponsorLink(
            era_id=era.era_id,
            brand_id=brand_a.brand_id,
            rank_order=1,
            prominence_percent=100
        )
        db_session.add(link)
    
    await db_session.commit()
    
    # Refresh IDs
    brand_a_id = brand_a.brand_id
    brand_b_id = brand_b.brand_id

    # 2. Execute Merge
    result = await SponsorService.merge_brands(
        session=db_session,
        source_brand_id=brand_a_id,
        target_brand_id=brand_b_id
    )
    
    assert result["repointed_links"] == 5
    assert result["total_links_affected"] == 5

    # 3. Verify
    # Brand A should be gone
    a_check = await db_session.get(SponsorBrand, brand_a_id)
    assert a_check is None

    # Links should now point to Brand B
    stmt = select(TeamSponsorLink).where(TeamSponsorLink.brand_id == brand_b_id)
    links = (await db_session.execute(stmt)).scalars().all()
    assert len(links) == 5
    for link in links:
        assert link.brand_id == brand_b_id


@pytest.mark.asyncio
async def test_merge_brands_conflict(db_session: AsyncSession):
    """
    Test Case 2: Conflict Merge (Both A and B on same ERA).
    Prominence should sum, Rank should take best (min).
    """
    # 1. Setup Data
    master = SponsorMaster(legal_name="Merge Test 2")
    db_session.add(master)
    await db_session.flush()

    brand_a = SponsorBrand(master_id=master.master_id, brand_name="Brand A Conflict", default_hex_color="#000000")
    brand_b = SponsorBrand(master_id=master.master_id, brand_name="Brand B Conflict", default_hex_color="#FFFFFF")
    db_session.add(brand_a)
    db_session.add(brand_b)
    await db_session.flush()

    # Create dummy parent node for eras
    node = TeamNode(legal_name="Merge Node 2", founding_year=1990)
    db_session.add(node)
    await db_session.flush()

    # Create Shared Era
    era = TeamEra(
        node_id=node.node_id,
        registered_name="Conflict Era", 
        season_year=2020, 
        valid_from=date(2020, 1, 1),
        uci_code="CFT", 
        country_code="FRA"
    )
    db_session.add(era)
    await db_session.flush()
    era_id = era.era_id

    # Link A (Source): 30%, Rank 2
    link_a = TeamSponsorLink(
        era_id=era_id,
        brand_id=brand_a.brand_id,
        rank_order=2,
        prominence_percent=30
    )
    db_session.add(link_a)

    # Link B (Target): 40%, Rank 1
    link_b = TeamSponsorLink(
        era_id=era_id,
        brand_id=brand_b.brand_id,
        rank_order=1,
        prominence_percent=40
    )
    db_session.add(link_b)
    await db_session.commit()

    # 2. Execute Merge
    result = await SponsorService.merge_brands(
        session=db_session,
        source_brand_id=brand_a.brand_id,
        target_brand_id=brand_b.brand_id
    )
    
    assert result["consolidated_links"] == 1
    assert result["total_links_affected"] == 1

    # 3. Verify Logic
    # Should only be one link for this Era + Brand B
    stmt = select(TeamSponsorLink).where(
        TeamSponsorLink.era_id == era_id,
        TeamSponsorLink.brand_id == brand_b.brand_id
    )
    link = (await db_session.execute(stmt)).scalar_one_or_none()
    
    assert link is not None
    # Prominence should be 30 + 40 = 70
    assert link.prominence_percent == 70
    # Rank should be min(1, 2) = 1
    assert link.rank_order == 1
    
    # Source link should be gone (covered by standard test, but good check)
    stmt_a = select(TeamSponsorLink).where(
        TeamSponsorLink.era_id == era_id,
        TeamSponsorLink.brand_id == brand_a.brand_id
    )
    link_a_check = (await db_session.execute(stmt_a)).scalar_one_or_none()
    assert link_a_check is None
