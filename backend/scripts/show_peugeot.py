#!/usr/bin/env python3
"""Quick script to show what Peugeot sponsor context looks like."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.database import async_session_maker
from app.models.sponsor import SponsorMaster, SponsorBrand

async def main():
    async with async_session_maker() as session:
        # Fetch Peugeot sponsor(s)
        stmt = (
            select(SponsorMaster)
            .options(selectinload(SponsorMaster.brands).selectinload(SponsorBrand.team_links))
            .where(SponsorMaster.legal_name.ilike("%Peugeot%"))
            .order_by(SponsorMaster.legal_name)
        )
        result = await session.execute(stmt)
        masters = result.scalars().all()
        
        # Format like the consolidation script does
        context = []
        for master in masters:
            brands_info = []
            for brand in master.brands:
                link_count = len(brand.team_links)
                brands_info.append({
                    "id": str(brand.brand_id),
                    "n": brand.brand_name,
                    "dn": brand.display_name,
                    "uses": link_count
                })
            
            context.append({
                "id": str(master.master_id),
                "n": master.legal_name,
                "sector": master.industry_sector,
                "url": master.source_url,
                "notes": master.source_notes,
                "brands": brands_info
            })
        
        print(json.dumps(context, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
