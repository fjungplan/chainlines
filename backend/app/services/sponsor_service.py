from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.models.sponsor import SponsorMaster, SponsorBrand
from app.schemas.sponsors import (
    SponsorMasterCreate, SponsorMasterUpdate,
    SponsorBrandCreate, SponsorBrandUpdate,
    SponsorMasterListResponse
)

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
    async def create_master(session: AsyncSession, data: SponsorMasterCreate, user_id: UUID) -> SponsorMaster:
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
        user_id: UUID
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
        user_id: UUID
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
