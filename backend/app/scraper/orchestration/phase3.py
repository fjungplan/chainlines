"""Phase 3: Lineage Connection."""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.scraper.llm.prompts import ScraperPrompts
from app.services.audit_log_service import AuditLogService
from app.models.enums import EditAction, EditStatus
from app.scraper.monitor import ScraperStatusMonitor

from app.scraper.utils.sse import sse_manager

logger = logging.getLogger(__name__)
CONFIDENCE_THRESHOLD = 0.90

class OrphanDetector:
    """Detects orphan nodes that may need lineage connections."""
    
    def __init__(self, session: AsyncSession, max_gap_years: int = 2):
        self._session = session
        self._max_gap = max_gap_years
    
    async def get_orphan_candidates(self) -> List[Dict[str, Any]]:
        """Fetch teams from DB and find candidates."""
        from sqlalchemy import select
        from app.models.team import TeamNode
        
        stmt = select(TeamNode)
        result = await self._session.execute(stmt)
        nodes = result.scalars().all()
        
        # Convert to dict format expected by find_candidates
        teams_data = []
        for node in nodes:
            data = {
                "id": node.node_id,
                "name": node.legal_name,
                "start_year": node.founding_year,
                "uci": node.latest_uci_code,
                # Note: history content ideally comes from specific TeamEras
                # For now we leave it None to avoid complex joins in this detector
                "wikipedia_history_content": None 
            }
            if node.dissolution_year:
                data["end_year"] = node.dissolution_year
            
            teams_data.append(data)
            
        return self.find_candidates(teams_data)

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
                # Skip self-matches or nonsense
                if ended["id"] == started["id"]:
                    continue

                # Calculate gap: Start year of successor - End year of predecessor
                gap = started["start_year"] - ended["end_year"]
                
                # Check if gap is within range (0 < gap <= max_gap)
                if 0 < gap <= self._max_gap:
                    candidates.append({
                        "predecessor": ended,
                        "successor": started,
                        "gap_years": gap
                    })
        
        return candidates

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
        successor_info: str,
        predecessor_history: Optional[str] = None,
        successor_history: Optional[str] = None
    ) -> None:
        """Analyze and create lineage connection."""
        decision = await self._prompts.decide_lineage(
            predecessor_info=predecessor_info,
            successor_info=successor_info,
            predecessor_history=predecessor_history,
            successor_history=successor_history
        )
        
        if decision.event_type is None:
            logger.info(f"    - Decision: NO_CONNECTION (Confidence: {decision.confidence*100:.1f}%)")
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
        
        logger.info(f"    - Created {decision.event_type.value} connection ({status.value})")
        if decision.reasoning:
             logger.info(f"    - Reasoning: {decision.reasoning[:120]}...")


class LineageOrchestrator:
    """Orchestrates Phase 3 processing."""
    
    def __init__(
        self,
        service: LineageConnectionService,
        monitor: Optional[ScraperStatusMonitor] = None
    ):
        self._service = service
        self._monitor = monitor
        self._run_id = str(monitor.run_id) if monitor else None

    async def _emit_progress(self, current: int, total: int):
        """Emit progress event via SSE."""
        if not self._run_id:
            return
        await sse_manager.emit(self._run_id, "progress", {
            "phase": 3,
            "current": current,
            "total": total,
            "percent": round(current / total * 100, 1)
        })

    async def run(self, candidates: List[Dict[str, Any]]) -> None:
        """Process candidate pairs for lineage connections."""
        if not candidates:
            logger.info("Phase 3: No lineage candidates found.")
            return

        logger.info(f"Phase 3: Starting analysis of {len(candidates)} potential connections")
        
        for i, pair in enumerate(candidates, 1):
            if self._monitor:
                await self._monitor.check_status()
            
            await self._emit_progress(i, len(candidates))
            
            pred = pair["predecessor"]
            succ = pair["successor"]
            
            logger.info(f"Pair {i}/{len(candidates)}: {pred['name']} ([{pred['end_year']}]) -> {succ['name']} ([{succ['start_year']}])")
            
            try:
                await self._service.connect(
                    predecessor_info=f"Team: {pred['name']}, UCI: {pred.get('uci')}, Year: {pred['end_year']}",
                    successor_info=f"Team: {succ['name']}, UCI: {succ.get('uci')}, Year: {succ['start_year']}",
                    predecessor_history=pred.get("wikipedia_history_content"),
                    successor_history=succ.get("wikipedia_history_content")
                )
            except Exception as e:
                logger.error(f"    - Error analyzing pair: {e}")
                continue

        logger.info("Phase 3: Lineage analysis complete.")
