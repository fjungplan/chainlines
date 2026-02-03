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
        await session.flush()
        await session.refresh(master)
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
        await session.flush()
        await session.refresh(master)
        return master

    @staticmethod
    async def delete_master(session: AsyncSession, master_id: UUID) -> bool:
        master = await SponsorService.get_master_by_id(session, master_id)
        if not master:
            return False
        
        # Safeguard: Do not allow deletion if brands exist
        # This prevents accidental cascade deletion of the entire sponsor tree
        if master.brands and len(master.brands) > 0:
            raise ValueError(f"Cannot delete sponsor master '{master.legal_name}' because it still has {len(master.brands)} brands. Delete or transfer these brands first.")
        
        await session.delete(master)
        await session.flush()
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
        await session.flush()
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
        await session.flush()
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
        await session.flush()
        return True

    @staticmethod
    async def search_masters(session: AsyncSession, query: str, limit: int = 20) -> List[SponsorMaster]:
        """
        Search sponsor masters by name or brand name (accent-insensitive).
        
        Returns deduplicated results even when multiple brands match.
        """
        from sqlalchemy import or_, func, distinct
        from app.models.sponsor import SponsorBrand
        
        # Normalize search term for accent insensitivity
        search_query = f"%{query}%"
        unaccented_query = func.unaccent(search_query)
        
        stmt = (
            select(SponsorMaster)
            .distinct(SponsorMaster.master_id)  # Prevent duplicates when multiple brands match
            .options(selectinload(SponsorMaster.brands))
            .where(
                or_(
                    # Search sponsor master name
                    func.unaccent(SponsorMaster.legal_name).ilike(unaccented_query),
                    # Search brand names using relationship
                    SponsorMaster.brands.any(func.unaccent(SponsorBrand.brand_name).ilike(unaccented_query)),
                    SponsorMaster.brands.any(func.unaccent(SponsorBrand.display_name).ilike(unaccented_query))
                )
            )
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def search_brands(session: AsyncSession, query: str, limit: int = 20) -> List[SponsorBrand]:
        from sqlalchemy import or_, func
        
        search_query = f"%{query}%"
        unaccented_query = func.unaccent(search_query)
        
        stmt = (
            select(SponsorBrand)
            .where(
                or_(
                    func.unaccent(SponsorBrand.brand_name).ilike(unaccented_query),
                    func.unaccent(SponsorBrand.display_name).ilike(unaccented_query)
                )
            )
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_era_sponsor_links(session: AsyncSession, era_id: UUID) -> List[TeamSponsorLink]:
        stmt = (
            select(TeamSponsorLink)
            .options(selectinload(TeamSponsorLink.brand))
            .where(TeamSponsorLink.era_id == era_id)
        )
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

        # Check total prominence - REMOVED for flexibility
        # existing_links = await SponsorService.get_era_sponsor_links(session, era_id)
        # current_total = sum(l.prominence_percent for l in existing_links)
        # if current_total + prominence_percent > 100:
        #      raise ValidationException(f"Total prominence cannot exceed 100%. Current: {current_total}%, Adding: {prominence_percent}%")

        link = TeamSponsorLink(
            era_id=era_id,
            brand_id=brand_id,
            rank_order=rank_order,
            prominence_percent=prominence_percent,
            created_by=user_id,
            last_modified_by=user_id
        )
        session.add(link)
        await session.flush()
        await session.refresh(link)
        return link

    @staticmethod
    async def update_sponsor_link(
        session: AsyncSession,
        link_id: UUID,
        prominence_percent: int,
        rank_order: int,
        hex_color_override: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> Optional[TeamSponsorLink]:
        stmt = select(TeamSponsorLink).where(TeamSponsorLink.link_id == link_id)
        link = (await session.execute(stmt)).scalar_one_or_none()
        
        if not link:
            return None

        # Validate prominence
        if prominence_percent <= 0 or prominence_percent > 100:
            raise ValidationException("Prominence must be between 1 and 100")

        # Check rank collision if rank changed
        if link.rank_order != rank_order:
             stmt = select(TeamSponsorLink).where(
                TeamSponsorLink.era_id == link.era_id, 
                TeamSponsorLink.rank_order == rank_order
            )
             existing_rank = (await session.execute(stmt)).scalar_one_or_none()
             if existing_rank:
                 raise ValidationException(f"Rank {rank_order} is already occupied for this era")

        link.prominence_percent = prominence_percent
        link.rank_order = rank_order
        link.hex_color_override = hex_color_override
        link.last_modified_by = user_id

        await session.flush()
        await session.refresh(link)
        return link

    @staticmethod
    async def replace_era_sponsor_links(
        session: AsyncSession,
        era_id: UUID,
        links_data: List[dict],
        user_id: Optional[UUID] = None
    ) -> List[TeamSponsorLink]:
        """
        Replace all sponsor links for an era with a new set.
        strictly validates total prominence == 100% for the new set.
        """
        # 1. Validate constraints of the new set
        total_prominence = sum(l['prominence_percent'] for l in links_data)
        if abs(total_prominence - 100) > 0.1: # float tolerance just in case, though int used
             raise ValidationException(f"Total prominence must be exactly 100%. Got {total_prominence}%")
        
        ranks = [l['rank_order'] for l in links_data]
        if len(ranks) != len(set(ranks)):
             raise ValidationException("Duplicate rank orders are not allowed")
             
        # 2. Delete existing links
        stmt = select(TeamSponsorLink).where(TeamSponsorLink.era_id == era_id)
        existing_links = (await session.execute(stmt)).scalars().all()
        
        for link in existing_links:
            await session.delete(link)
            
        # Flush to ensure deletions are processed before insertions to avoid UniqueConstraint violations
        await session.flush()
            
        # 3. Create new links
        new_links = []
        for data in links_data:
            link = TeamSponsorLink(
                era_id=era_id,
                brand_id=data['brand_id'],
                # If these come from creating a new list, they might not have link_id yet, 
                # or if we are just re-creating, we generate new IDs. 
                # Simpler to treat as new inserts.
                rank_order=data['rank_order'],
                prominence_percent=data['prominence_percent'],
                hex_color_override=data.get('hex_color_override'),
                created_by=user_id,
                last_modified_by=user_id
            )
            session.add(link)
            new_links.append(link)
            
        await session.flush()
        
        # Re-fetch with eager loading for response serialization
        # This prevents "Lazy load operation of attribute..." errors during Pydantic validation
        stmt = (
            select(TeamSponsorLink)
            .options(selectinload(TeamSponsorLink.brand))
            .where(TeamSponsorLink.era_id == era_id)
            .order_by(TeamSponsorLink.rank_order)
        )
        final_links = (await session.execute(stmt)).scalars().all()
        
        return final_links

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

    @staticmethod
    async def remove_sponsor_from_era(session: AsyncSession, link_id: UUID) -> bool:
        stmt = select(TeamSponsorLink).where(TeamSponsorLink.link_id == link_id)
        result = await session.execute(stmt)
        link = result.scalar_one_or_none()
        
        if not link:
            return False
            
        await session.delete(link)
        await session.flush()
        return True

    @staticmethod
    async def merge_brands(
        session: AsyncSession, 
        source_brand_id: UUID, 
        target_brand_id: UUID
    ) -> dict:
        """
        Destructive merge of Source -> Target.
        1. Repoint all links from Source to Target.
        2. Resolve conflicts (same Era): Sum prominence, take best rank.
        3. Delete Source Brand.
        
        Returns details about the operations performed.
        """
        # Fetch Source Links
        stmt = select(TeamSponsorLink).where(TeamSponsorLink.brand_id == source_brand_id)
        source_links = (await session.execute(stmt)).scalars().all()
        
        repointed_count = 0
        consolidated_count = 0
        
        for source_link in source_links:
            # Check for conflict in this Era
            stmt_conflict = select(TeamSponsorLink).where(
                TeamSponsorLink.era_id == source_link.era_id,
                TeamSponsorLink.brand_id == target_brand_id
            )
            target_link = (await session.execute(stmt_conflict)).scalar_one_or_none()
            
            if target_link:
                # CONFLICT: Merge into Target
                # 1. Sum Prominence
                new_prominence = target_link.prominence_percent + source_link.prominence_percent
                target_link.prominence_percent = min(new_prominence, 100) # Cap at 100 logic-wise, though validation triggers
                
                # 2. Take Best Rank (Min)
                target_link.rank_order = min(target_link.rank_order, source_link.rank_order)
                
                # 3. Delete Source Link
                await session.delete(source_link)
                consolidated_count += 1
            else:
                # NO CONFLICT: Repoint
                source_link.brand_id = target_brand_id
                repointed_count += 1

        # Flush link changes
        await session.flush()
        
        # Delete Source Brand
        stmt_brand = select(SponsorBrand).where(SponsorBrand.brand_id == source_brand_id)
        source_brand = (await session.execute(stmt_brand)).scalar_one_or_none()
        
        if source_brand:
            await session.delete(source_brand)
            
        await session.flush()
        
        return {
            "repointed_links": repointed_count,
            "consolidated_links": consolidated_count,
            "total_links_affected": repointed_count + consolidated_count
        }
