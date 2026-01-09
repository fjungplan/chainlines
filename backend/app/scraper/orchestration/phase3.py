"""Phase 3: Lineage Detection - Redesigned.

Analyzes boundary nodes (those that end or start at year transitions)
to detect lineage events using Wikipedia evidence.
"""
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import TeamNode, TeamEra
from app.scraper.llm.prompts import ScraperPrompts
from app.services.audit_log_service import AuditLogService
from app.models.enums import EditAction, EditStatus
from app.scraper.monitor import ScraperStatusMonitor

logger = logging.getLogger(__name__)
CONFIDENCE_THRESHOLD = 0.90


class BoundaryNodeDetector:
    """
    Detects boundary nodes - teams that end or start at year transitions.
    
    These are candidates for lineage analysis:
    - Ending nodes: Have an era in year X but not in year X+1
    - Starting nodes: Have an era in year X+1 but not in year X
    """
    
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_boundary_nodes(
        self,
        transition_year: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find nodes that end or start at a year transition.
        
        Args:
            transition_year: The year where we look for endings (e.g., 2025)
                             Starting year is transition_year + 1 (e.g., 2026)
        
        Returns:
            Dict with "ending" and "starting" lists of node info
        """
        stmt = select(TeamNode).options(selectinload(TeamNode.eras))
        result = await self._session.execute(stmt)
        nodes = result.scalars().all()
        
        next_year = transition_year + 1
        
        ending_nodes = []
        starting_nodes = []
        
        for node in nodes:
            if not node.eras:
                continue
            
            era_years = {era.season_year for era in node.eras}
            
            # Node ends if it has era in transition_year but not next_year
            if transition_year in era_years and next_year not in era_years:
                ending_nodes.append(self._node_to_dict(node, transition_year))
            
            # Node starts if it has era in next_year but not transition_year
            if next_year in era_years and transition_year not in era_years:
                starting_nodes.append(self._node_to_dict(node, next_year))
        
        logger.info(
            f"Boundary analysis for {transition_year}→{next_year}: "
            f"{len(ending_nodes)} ending, {len(starting_nodes)} starting"
        )
        
        return {
            "ending": ending_nodes,
            "starting": starting_nodes
        }
    
    def _node_to_dict(self, node: TeamNode, reference_year: int) -> Dict[str, Any]:
        """Convert TeamNode to dict for lineage analysis."""
        return {
            "id": node.node_id,
            "name": node.legal_name,
            "year": reference_year,
            "uci_code": node.latest_uci_code,
            "wikipedia_summary": node.wikipedia_summary,
            "_node": node  # Reference for dissolution_year updates
        }


class LineageExtractor:
    """
    Extracts lineage events from Wikipedia content using LLM.
    
    Analyzes each boundary node individually (not pairs) to find
    mentions of predecessors/successors.
    """
    
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
    
    async def analyze_ending_node(
        self,
        node_info: Dict[str, Any],
        available_teams: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze an ending node to find what it became.
        
        Args:
            node_info: Dict with team info including wikipedia_summary
            available_teams: Optional list of team names from DB for LLM to pick from
        
        Returns list of lineage events found (SUCCEEDED_BY, JOINED, SPLIT_INTO, etc.)
        """
        if not node_info.get("wikipedia_summary"):
            logger.info(f"  Skipping {node_info['name']} - no Wikipedia content")
            return []
        
        events = await self._prompts.extract_lineage_events(
            team_name=node_info["name"],
            context="ending",
            year=node_info["year"],
            wikipedia_content=node_info["wikipedia_summary"],
            available_teams=available_teams or []
        )
        
        return events or []
    
    async def analyze_starting_node(
        self,
        node_info: Dict[str, Any],
        available_teams: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze a starting node to find where it came from.
        
        Args:
            node_info: Dict with team info including wikipedia_summary
            available_teams: Optional list of team names from DB for LLM to pick from
        
        Returns list of lineage events found (SUCCESSOR_OF, BREAKAWAY_FROM, MERGER_OF, etc.)
        """
        if not node_info.get("wikipedia_summary"):
            logger.info(f"  Skipping {node_info['name']} - no Wikipedia content")
            return []
        
        events = await self._prompts.extract_lineage_events(
            team_name=node_info["name"],
            context="starting",
            year=node_info["year"],
            wikipedia_content=node_info["wikipedia_summary"],
            available_teams=available_teams or []
        )
        
        return events or []
    
    async def create_lineage_record(
        self,
        source_node: Dict[str, Any],
        event: Dict[str, Any]
    ) -> None:
        """Create an audit log entry for a detected lineage event.
        
        When status is APPROVED, also inserts the actual LineageEvent record.
        """
        from sqlalchemy import select
        from app.models.lineage import LineageEvent
        from app.models.team import TeamNode
        from app.models.enums import LineageEventType
        
        status = (
            EditStatus.APPROVED if event.get("confidence", 0) >= CONFIDENCE_THRESHOLD
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
                "event_type": event.get("event_type"),
                "source_team": source_node["name"],
                "target_team": event.get("target_name"),
                "year": source_node["year"],
                "reasoning": event.get("reasoning"),
                "confidence": event.get("confidence")
            },
            status=status
        )
        
        # If APPROVED, create the actual LineageEvent record
        if status == EditStatus.APPROVED:
            target_name = event.get("target_name")
            if target_name:
                # Look up the target team node - try exact match first, then ILIKE
                # First try exact match on legal_name
                stmt = select(TeamNode).where(TeamNode.legal_name == target_name)
                result = await self._session.execute(stmt)
                target_node = result.scalar_one_or_none()
                
                # If no exact match, try ILIKE on legal_name
                if not target_node:
                    stmt = select(TeamNode).where(TeamNode.legal_name.ilike(f"%{target_name}%"))
                    result = await self._session.execute(stmt)
                    target_node = result.scalars().first()
                
                # Fallback: search by TeamEra.registered_name (handles temporal naming)
                # e.g., "Lotto" (2025 name) → "Lotto - Intermarché" (2026 name)
                if not target_node:
                    from app.models.team import TeamEra
                    from sqlalchemy.orm import selectinload
                    stmt = select(TeamEra).where(
                        TeamEra.registered_name.ilike(f"%{target_name}%")
                    ).options(selectinload(TeamEra.node))
                    result = await self._session.execute(stmt)
                    era = result.scalars().first()
                    if era and era.node:
                        target_node = era.node
                        logger.info(f"    ↳ Resolved '{target_name}' via era name → {target_node.legal_name}")
                
                if target_node:
                    # Map event types to LineageEventType enum
                    # Available: LEGAL_TRANSFER, SPIRITUAL_SUCCESSION, MERGE, SPLIT
                    event_type_map = {
                        "JOINED": LineageEventType.MERGE,
                        "MERGED_WITH": LineageEventType.MERGE,
                        "MERGED": LineageEventType.MERGE,
                        "MERGER_OF": LineageEventType.MERGE,
                        "SUCCEEDED_BY": LineageEventType.LEGAL_TRANSFER,
                        "SUCCESSOR_OF": LineageEventType.LEGAL_TRANSFER,
                        "SPLIT_INTO": LineageEventType.SPLIT,
                        "BREAKAWAY_FROM": LineageEventType.SPLIT,
                        "FOLDED": LineageEventType.MERGE,  # Folded into nothing - treat as merge
                    }
                    lineage_type = event_type_map.get(event.get("event_type"), LineageEventType.LEGAL_TRANSFER)
                    
                    lineage_event = LineageEvent(
                        predecessor_node_id=source_node["node_id"],
                        successor_node_id=target_node.node_id,
                        event_year=source_node["year"],
                        event_type=lineage_type,
                        notes=event.get("reasoning"),
                        created_by=self._user_id
                    )
                    self._session.add(lineage_event)
                    logger.info(f"    ✓ Created LineageEvent record: {source_node['name']} → {target_node.legal_name}")
                else:
                    logger.warning(f"    ✗ Could not find target team '{target_name}' for LineageEvent")
        
        # Update dissolution_year on TeamNode when team folded
        event_type = event.get("event_type")
        if event_type in ("FOLDED", "MERGED", "JOINED"):
            node = source_node.get("_node")
            if node:
                node.dissolution_year = source_node["year"]
                logger.info(f"  Updated dissolution_year to {source_node['year']} for {source_node['name']}")
        
        logger.info(
            f"  Created {event.get('event_type')} event: "
            f"{source_node['name']} → {event.get('target_name')} ({status.value})"
        )


class LineageOrchestrator:
    """Orchestrates Phase 3 lineage detection."""
    
    def __init__(
        self,
        detector: BoundaryNodeDetector,
        extractor: LineageExtractor,
        session: AsyncSession,
        monitor: Optional[ScraperStatusMonitor] = None
    ):
        self._detector = detector
        self._extractor = extractor
        self._session = session
        self._monitor = monitor
    
    async def run(self, transition_year: int) -> None:
        """
        Run lineage detection for a year transition.
        
        Args:
            transition_year: The year to analyze (e.g., 2025 for 2025→2026 transition)
        """
        logger.info(f"Phase 3: Analyzing lineage for {transition_year}→{transition_year + 1}")
        
        # Step 1: Find boundary nodes
        boundaries = await self._detector.get_boundary_nodes(transition_year)
        
        ending_nodes = boundaries["ending"]
        starting_nodes = boundaries["starting"]
        
        total = len(ending_nodes) + len(starting_nodes)
        if total == 0:
            logger.info("Phase 3: No boundary nodes found")
            return
        
        processed = 0
        
        # Step 2: Analyze ending nodes (what did they become?)
        logger.info(f"Phase 3: Analyzing {len(ending_nodes)} ending nodes")
        for node in ending_nodes:
            if self._monitor:
                await self._monitor.check_status()
            
            logger.info(f"  Analyzing ending: {node['name']}")
            events = await self._extractor.analyze_ending_node(node)
            
            if events:
                logger.info(f"    Found {len(events)} lineage event(s)")
                for event in events:
                    logger.info(f"      - {event.get('event_type')}: {event.get('target_name')} (conf: {event.get('confidence')})")
                    await self._extractor.create_lineage_record(node, event)
            else:
                logger.info(f"    No lineage events detected by LLM")
            
            processed += 1
            await self._session.commit()
        
        # Step 3: Analyze starting nodes (where did they come from?)
        logger.info(f"Phase 3: Analyzing {len(starting_nodes)} starting nodes")
        for node in starting_nodes:
            if self._monitor:
                await self._monitor.check_status()
            
            logger.info(f"  Analyzing starting: {node['name']}")
            events = await self._extractor.analyze_starting_node(node)
            
            if events:
                logger.info(f"    Found {len(events)} lineage event(s)")
                for event in events:
                    logger.info(f"      - {event.get('event_type')}: {event.get('target_name')} (conf: {event.get('confidence')})")
                    await self._extractor.create_lineage_record(node, event)
            else:
                logger.info(f"    No lineage events detected by LLM")
            
            processed += 1
            await self._session.commit()
        
        logger.info(f"Phase 3: Complete. Analyzed {processed} boundary nodes.")
