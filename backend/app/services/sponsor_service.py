from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.models.sponsor import SponsorMaster, SponsorBrand, TeamSponsorLink
from app.schemas.sponsors import (
    SponsorMasterCreate, SponsorMasterUpdate,
    SponsorBrandCreate, SponsorBrandUpdate,
    SponsorMasterListResponse
)
from app.core.exceptions import ValidationException

class SponsorService:
    @staticmethod
    async def get_all_masters(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[SponsorMaster]:
        stmt = (
            select(SponsorMaster)
            .options(selectinload(SponsorMaster.brands))
            .order_by(SponsorMaster.legal_name)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_master_by_id(session: AsyncSession, master_id: UUID) -> Optional[SponsorMaster]:
        stmt = (
            select(SponsorMaster)
            .options(selectinload(SponsorMaster.brands))
            .where(SponsorMaster.master_id == master_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_master(session: AsyncSession, data: SponsorMasterCreate, user_id: Optional[UUID] = None) -> SponsorMaster:
        master = SponsorMaster(
            **data.model_dump(),
            created_by=user_id,
            last_modified_by=user_id
        )
        session.add(master)
        await session.commit()
        await session.refresh(master)
        # Refresh brands to return empty list correctly modeled
        await session.refresh(master, ['brands'])
        return master

    @staticmethod
    async def update_master(
        session: AsyncSession, 
        master_id: UUID, 
        data: SponsorMasterUpdate, 
        user_id: Optional[UUID] = None
    ) -> Optional[SponsorMaster]:
        master = await SponsorService.get_master_by_id(session, master_id)
        if not master:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(master, key, value)
        
        master.last_modified_by = user_id
        await session.commit()
        await session.refresh(master)
        return master

    @staticmethod
    async def delete_master(session: AsyncSession, master_id: UUID) -> bool:
        master = await SponsorService.get_master_by_id(session, master_id)
        if not master:
            return False
        
        await session.delete(master)
        await session.commit()
        return True

    @staticmethod
    async def add_brand(
        session: AsyncSession, 
        master_id: UUID, 
        data: SponsorBrandCreate, 
        user_id: Optional[UUID] = None
    ) -> Optional[SponsorBrand]:
        master = await SponsorService.get_master_by_id(session, master_id)
        if not master:
            return None
            
        brand = SponsorBrand(
            **data.model_dump(),
            master_id=master_id,
            created_by=user_id,
            last_modified_by=user_id
        )
        session.add(brand)
        await session.commit()
        await session.refresh(brand)
        return brand

    @staticmethod
    async def update_brand(
        session: AsyncSession, 
        brand_id: UUID, 
        data: SponsorBrandUpdate, 
        user_id: UUID
    ) -> Optional[SponsorBrand]:
        stmt = select(SponsorBrand).where(SponsorBrand.brand_id == brand_id)
        result = await session.execute(stmt)
        brand = result.scalar_one_or_none()
        
        if not brand:
            return None
            
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(brand, key, value)
            
        brand.last_modified_by = user_id
        await session.commit()
        await session.refresh(brand)
        return brand
    
    @staticmethod
    async def delete_brand(session: AsyncSession, brand_id: UUID) -> bool:
        stmt = select(SponsorBrand).where(SponsorBrand.brand_id == brand_id)
        result = await session.execute(stmt)
        brand = result.scalar_one_or_none()
        
        if not brand:
            return False
            
        await session.delete(brand)
        await session.commit()
        return True

    @staticmethod
    async def search_masters(session: AsyncSession, query: str, limit: int = 20) -> List[SponsorMaster]:
        stmt = (
            select(SponsorMaster)
            .options(selectinload(SponsorMaster.brands))
            .where(SponsorMaster.legal_name.ilike(f"%{query}%"))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def search_brands(session: AsyncSession, query: str, limit: int = 20) -> List[SponsorBrand]:
        stmt = (
            select(SponsorBrand)
            .where(SponsorBrand.brand_name.ilike(f"%{query}%"))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_era_sponsor_links(session: AsyncSession, era_id: UUID) -> List[TeamSponsorLink]:
        stmt = select(TeamSponsorLink).where(TeamSponsorLink.era_id == era_id)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def link_sponsor_to_era(
        session: AsyncSession, 
        era_id: UUID, 
        brand_id: UUID, 
        rank_order: int, 
        prominence_percent: int,
        user_id: Optional[UUID] = None
    ) -> TeamSponsorLink:
        # Validate prominence
        if prominence_percent <= 0 or prominence_percent > 100:
            raise ValidationException("Prominence must be between 1 and 100")
            
        # Check if rank already exists
        stmt = select(TeamSponsorLink).where(
            TeamSponsorLink.era_id == era_id, 
            TeamSponsorLink.rank_order == rank_order
        )
        existing_rank = (await session.execute(stmt)).scalar_one_or_none()
        if existing_rank:
             raise ValidationException(f"Rank {rank_order} is already occupied for this era")

        # Check total prominence
        existing_links = await SponsorService.get_era_sponsor_links(session, era_id)
        current_total = sum(l.prominence_percent for l in existing_links)
        if current_total + prominence_percent > 100:
             raise ValidationException(f"Total prominence cannot exceed 100%. Current: {current_total}%, Adding: {prominence_percent}%")

        link = TeamSponsorLink(
            era_id=era_id,
            brand_id=brand_id,
            rank_order=rank_order,
            prominence_percent=prominence_percent,
            created_by=user_id,
            last_modified_by=user_id
        )
        session.add(link)
        await session.commit()
        await session.refresh(link)
        return link

    @staticmethod
    async def validate_era_sponsors(session: AsyncSession, era_id: UUID) -> dict:
        links = await SponsorService.get_era_sponsor_links(session, era_id)
        total = sum(l.prominence_percent for l in links)
        return {
            "valid": total <= 100,
            "total_percent": total,
            "sponsor_count": len(links),
            "remaining_percent": 100 - total
        }

    @staticmethod
    async def get_era_jersey_composition(session: AsyncSession, era_id: UUID) -> List[dict]:
        stmt = (
            select(TeamSponsorLink)
            .options(selectinload(TeamSponsorLink.brand))
            .where(TeamSponsorLink.era_id == era_id)
            .order_by(TeamSponsorLink.rank_order)
        )
        result = await session.execute(stmt)
        links = result.scalars().all()
        
        return [
            {
                "brand_name": link.brand.brand_name,
                "color": link.hex_color_override or link.brand.default_hex_color,
                "prominence_percent": link.prominence_percent,
                "rank_order": link.rank_order
            }
            for link in links
        ]
