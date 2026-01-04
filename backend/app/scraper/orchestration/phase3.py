"""Phase 3: Lineage Connection."""
from typing import List, Dict, Any

class OrphanDetector:
    """Detects orphan nodes that may need lineage connections."""
    
    def __init__(self, max_gap_years: int = 2):
        self._max_gap = max_gap_years
    
    def find_candidates(
        self,
        teams: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find teams that ended near when another started."""
        candidates = []
        
        ended_teams = [t for t in teams if "end_year" in t]
        started_teams = [t for t in teams if "start_year" in t]
        
        for ended in ended_teams:
            for started in started_teams:
                # Calculate gap: Start year of successor - End year of predecessor
                gap = started["start_year"] - ended["end_year"]
                
                # Check if gap is within range (0 < gap <= max_gap)
                # gap=1 means successor started the very next season (e.g. 2022 -> 2023)
                if 0 < gap <= self._max_gap:
                    candidates.append({
                        "predecessor": ended,
                        "successor": started,
                        "gap_years": gap
                    })
        
        return candidates

import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.scraper.llm.prompts import ScraperPrompts
from app.services.audit_log_service import AuditLogService
from app.models.enums import EditAction, EditStatus, LineageEventType

logger = logging.getLogger(__name__)
CONFIDENCE_THRESHOLD = 0.90

class LineageConnectionService:
    """Orchestrates Phase 3: Creating lineage connections."""
    
    def __init__(
        self,
        prompts: ScraperPrompts,
        audit_service: AuditLogService,
        session: AsyncSession,
        system_user_id: UUID
    ):
        self._prompts = prompts
        self._audit = audit_service
        self._session = session
        self._user_id = system_user_id
    
    async def connect(
        self,
        predecessor_info: str,
        successor_info: str
    ) -> None:
        """Analyze and create lineage connection."""
        decision = await self._prompts.decide_lineage(
            predecessor_info=predecessor_info,
            successor_info=successor_info
        )
        
        if decision.event_type is None:
            logger.info("LLM decided NO_CONNECTION (event_type=None). Skipping.")
            return

        status = (
            EditStatus.APPROVED if decision.confidence >= CONFIDENCE_THRESHOLD
            else EditStatus.PENDING
        )
        
        await self._audit.create_edit(
            session=self._session,
            user_id=self._user_id,
            entity_type="LineageEvent",
            entity_id=None,
            action=EditAction.CREATE,
            old_data=None,
            new_data={
                "event_type": decision.event_type.value,
                "predecessor_ids": [str(id) for id in decision.predecessor_ids],
                "successor_ids": [str(id) for id in decision.successor_ids],
                "reasoning": decision.reasoning
            },
            status=status
        )
        
        logger.info(f"Created lineage {decision.event_type.value} ({status.value})")
