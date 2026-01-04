"""Phase 2: Team Node Assembly."""
import logging
from typing import List
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.scraper.sources.cyclingflash import ScrapedTeamData
from app.services.audit_log_service import AuditLogService
from app.models.enums import EditAction, EditStatus

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.90


class ProminenceCalculator:
    """Calculates sponsor prominence percentages."""
    
    RULES = {
        1: [100],
        2: [60, 40],
        3: [40, 30, 30],
        4: [40, 20, 20, 20],
    }
    
    @classmethod
    def calculate(cls, sponsors: List[str]) -> List[int]:
        """Calculate prominence for each sponsor.
        
        Args:
            sponsors: List of sponsor names
            
        Returns:
            List of prominence percentages (must sum to 100)
        """
        count = len(sponsors)
        
        if count == 0:
            return []
        
        if count in cls.RULES:
            return cls.RULES[count]
        
        # 5+ sponsors: extend pattern (first gets 40, rest split evenly)
        first = 40
        remaining = 100 - first
        each = remaining // (count - 1)
        last_adjustment = remaining - (each * (count - 1))
        
        result = [first] + [each] * (count - 2) + [each + last_adjustment]
        return result


class TeamAssemblyService:
    """Orchestrates Phase 2: Team and Era creation."""
    
    def __init__(
        self,
        audit_service: AuditLogService,
        session: AsyncSession,
        system_user_id: UUID
    ):
        self._audit = audit_service
        self._session = session
        self._user_id = system_user_id
    
    async def create_team_era(
        self,
        data: ScrapedTeamData,
        confidence: float
    ) -> None:
        """Create TeamNode/TeamEra via AuditLog.
        
        Args:
            data: Scraped team data
            confidence: LLM confidence score (0.0-1.0)
        """
        status = (
            EditStatus.APPROVED if confidence >= CONFIDENCE_THRESHOLD
            else EditStatus.PENDING
        )
        
        # Build the edit payload
        new_data = {
            "registered_name": data.name,
            "season_year": data.season_year,
            "uci_code": data.uci_code,
            "tier_level": self._parse_tier(data.tier),
            "valid_from": f"{data.season_year}-01-01",
            "sponsors": [
                {"name": s, "prominence": p}
                for s, p in zip(
                    data.sponsors,
                    ProminenceCalculator.calculate(data.sponsors)
                )
            ]
        }
        
        await self._audit.create_edit(
            session=self._session,
            user_id=self._user_id,
            entity_type="TeamEra",
            entity_id=None,  # New entity
            action=EditAction.CREATE,
            old_data=None,
            new_data=new_data,
            status=status
        )
        
        logger.info(f"Created edit for {data.name} ({status.value})")
    
    def _parse_tier(self, tier: str | None) -> int | None:
        """Convert tier string to level.
        
        Args:
            tier: Tier string (e.g., "WorldTour", "ProTeam")
            
        Returns:
            Tier level (1-3) or None
        """
        if not tier:
            return None
        tier_map = {"WorldTour": 1, "ProTeam": 2, "Continental": 3}
        return tier_map.get(tier)
