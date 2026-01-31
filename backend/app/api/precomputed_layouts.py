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

import logging
logger = logging.getLogger(__name__)

@router.get("/precomputed-layouts")
async def get_precomputed_layouts(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    logger.info("Handling GET /api/v1/precomputed-layouts")
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
        # Use node_ids csv as key to match frontend's simple hash
        fingerprint = layout.data_fingerprint
        if not fingerprint or not isinstance(fingerprint, dict):
            continue
            
        node_ids = fingerprint.get("node_ids")
        if not node_ids or not isinstance(node_ids, list):
            continue
        
        # Convert to strings (in case they're UUIDs) and sort
        node_id_strings = [str(nid) for nid in node_ids]
        response[layout.family_hash] = {
            "layout_data": layout.layout_data,
            "score": layout.score,
            "optimized_at": layout.optimized_at.isoformat() if layout.optimized_at else None,
            "data_fingerprint": fingerprint
        }
        
    return response
