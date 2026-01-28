"""
Public API for retrieving precomputed layouts.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_db
from app.models.precomputed_layout import PrecomputedLayout

router = APIRouter(tags=["public"]) # Prefix handled in main.py

@router.get("/precomputed-layouts")
async def get_precomputed_layouts(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all precomputed layouts.
    
    Returns:
        Dict mapping family_hash -> layout object
    """
    # Fetch all valid layouts
    stmt = select(PrecomputedLayout)
    result = await db.execute(stmt)
    layouts = result.scalars().all()
    
    response = {}
    for layout in layouts:
        response[layout.family_hash] = {
            "layout_data": layout.layout_data,
            "score": layout.score,
            "optimized_at": layout.optimized_at.isoformat() if layout.optimized_at else None
        }
        
    return response
