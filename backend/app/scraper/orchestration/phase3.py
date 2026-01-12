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
from app.models.enums import EditAction, EditStatus, LineageEventType
from app.models.lineage import LineageEvent
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
            "node_id": node.node_id,
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
        available_teams: Optional[List[str]] = None,
        event_year_override: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze an ending node to find where it went.
        
        Args:
            node_info: Dict with team info including wikipedia_summary
            available_teams: Optional list of team names from DB for LLM to pick from
            event_year_override: Optional year to use for the event (e.g. node_year + 1)
        
        Returns list of lineage events found (SUCCEEDED_BY, JOINED, SPLIT_INTO, MERGED_WITH)
        """
        if not node_info.get("wikipedia_summary"):
            logger.info(f"  Skipping {node_info['name']} - no Wikipedia content")
            return []
        
        events = await self._prompts.extract_lineage_events(
            team_name=node_info["name"],
            context="ending",
            year=node_info["year"],
            wikipedia_content=node_info["wikipedia_summary"],
            available_teams=available_teams or [],
        )
        
        if events:
            for event in events:
                await self.create_lineage_record(
                    node_info, 
                    event, 
                    event_year_override=event_year_override
                )
        
        return events or []
    
    async def analyze_starting_node(
        self,
        node_info: Dict[str, Any],
        available_teams: Optional[List[str]] = None,
        event_year_override: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze a starting node to find where it came from.
        
        Args:
            node_info: Dict with team info including wikipedia_summary
            available_teams: Optional list of team names from DB for LLM to pick from
            event_year_override: Optional year to use for the event if different from node year
        
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
            available_teams=available_teams or [],
        )
        
        if events:
            for event in events:
                await self.create_lineage_record(
                    node_info, 
                    event,
                    event_year_override=event_year_override
                )
        
        return events or []
    
    async def create_lineage_record(
        self,
        source_node: Dict[str, Any],
        event: Dict[str, Any],
        event_year_override: Optional[int] = None
    ) -> None:
        """
        Create a LineageEvent record, with audit logging.
        
        Args:
            source_node: Dict with node_id, name, etc.
            event: Dict with event_type, target_name, confidence, reasoning
            event_year_override: Optional year to use for the event (e.g. for ending nodes, use year+1)
        """
        target_name = event.get("target_name")
        target_node = None
        
        # Step 1: Match target team name to DB node (if target specified)
        if target_name:
            # ASCII normalization approach: normalize both target and DB names
            import unicodedata
            from difflib import SequenceMatcher
            
            def normalize_to_ascii(s: str) -> str:
                """Normalize string to ASCII for comparison."""
                return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII').lower().strip()
            
            target_normalized = normalize_to_ascii(target_name)
            
            # Fetch all team names and find best match based on normalized comparison
            stmt = select(TeamNode)
            result = await self._session.execute(stmt)
            all_nodes = result.scalars().all()
            
            best_match = None
            best_score = 0.0
            
            for node in all_nodes:
                node_normalized = normalize_to_ascii(node.legal_name)
                score = SequenceMatcher(None, target_normalized, node_normalized).ratio()
                if score > best_score:
                    best_score = score
                    best_match = node
            
            # Also check era registered_name for temporal name resolution
            from app.models.team import TeamEra
            stmt_era = select(TeamEra).options(selectinload(TeamEra.node))
            result_era = await self._session.execute(stmt_era)
            all_eras = result_era.scalars().all()
            
            for era in all_eras:
                if era.registered_name and era.node:
                    era_normalized = normalize_to_ascii(era.registered_name)
                    score = SequenceMatcher(None, target_normalized, era_normalized).ratio()
                    if score > best_score:
                        best_score = score
                        best_match = era.node
            
            # Thresholds
            if best_score >= 0.95:
                target_node = best_match
                logger.info(f"    ↳ Matched '{target_name}' → {best_match.legal_name} (score: {best_score:.2f})")
            elif best_score >= 0.80:
                logger.warning(f"    ⚠ Low confidence match '{target_name}' → {best_match.legal_name} (score: {best_score:.2f}) - needs manual review")
            else:
                logger.warning(f"    ✗ No confident match for '{target_name}' (best: {best_match.legal_name if best_match else 'None'}, score: {best_score:.2f})")
        
        # Step 2: Validate - check for self-referencing events
        if target_node:
            source_node_id = str(source_node.get("node_id", ""))
            target_node_id = str(target_node.node_id)
            
            if source_node_id == target_node_id:
                logger.warning(
                    f"    ⚠️ Skipping self-referencing lineage event: "
                    f"{source_node['name']} → {target_node.legal_name} "
                    f"(same node_id: {source_node_id})"
                )
                return None
        
        # Step 3: Calculate event year and lineage type for idempotency check
        event_year = event_year_override if event_year_override is not None else source_node["year"]
        event_type_map = {
            "JOINED": LineageEventType.MERGE,
            "MERGED_WITH": LineageEventType.MERGE,
            "MERGED": LineageEventType.MERGE,
            "MERGER_OF": LineageEventType.MERGE,
            "SUCCEEDED_BY": LineageEventType.LEGAL_TRANSFER,
            "SUCCESSOR_OF": LineageEventType.LEGAL_TRANSFER,
            "SPLIT_INTO": LineageEventType.SPLIT,
            "BREAKAWAY_FROM": LineageEventType.SPLIT,
            "FOLDED": LineageEventType.MERGE,
        }
        lineage_type = event_type_map.get(event.get("event_type"), LineageEventType.LEGAL_TRANSFER)
        
        # Step 4: [IDEMPOTENCY] Check for existing duplicate event BEFORE creating audit log
        if target_node:
            stmt_dup = select(LineageEvent).where(
                LineageEvent.predecessor_node_id == source_node["node_id"],
                LineageEvent.successor_node_id == target_node.node_id,
                LineageEvent.event_type == lineage_type,
                LineageEvent.event_year == event_year
            )
            dup_result = await self._session.execute(stmt_dup)
            if dup_result.scalar_one_or_none():
                logger.warning(f"    ⏩ Skipping duplicate LineageEvent: {source_node['name']} → {target_node.legal_name} ({event_year})")
                return None
        
        # Step 4: Create audit log entry
        status = EditStatus.APPROVED if event.get("confidence", 0) >= CONFIDENCE_THRESHOLD else EditStatus.PENDING
        try:
            edit_context = {
                "source_node": source_node["name"],
                "target_team": event.get("target_name"),
                "event_type": event.get("event_type"),
                "confidence": event.get("confidence"),
                "reasoning": event.get("reasoning")
            }
            
            await self._audit.create_edit(
                session=self._session,
                user_id=self._user_id,
                entity_type="LineageEvent",
                entity_id=None,
                action=EditAction.CREATE,
                old_data=None,
                new_data=edit_context,
                status=status
            )
            
        except Exception as e:
            logger.error(f"Failed to create audit log for lineage event: {e}")
        
        # Step 5: If APPROVED, create the actual LineageEvent record
        if status == EditStatus.APPROVED and target_node:
            try:
                lineage_event = LineageEvent(
                    predecessor_node_id=source_node["node_id"],
                    successor_node_id=target_node.node_id,
                    event_year=event_year,
                    event_type=lineage_type,
                    notes=event.get("reasoning"),
                    created_by=self._user_id
                )
                self._session.add(lineage_event)
                logger.info(f"    ✓ Created LineageEvent record: {source_node['name']} → {target_node.legal_name}")
            except Exception as e:
                logger.error(f"    ⚠ Error creating LineageEvent: {e}")
                import traceback
                logger.error(traceback.format_exc())
        elif not target_node and target_name:
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
        
        # Gather all team names for LLM-guided matching
        # Include both ending and starting node names as potential targets
        all_team_names = [n["name"] for n in ending_nodes + starting_nodes]
        # Also fetch all active team names from DB for broader matching
        from sqlalchemy import select
        from app.models.team import TeamNode
        result = await self._session.execute(select(TeamNode.legal_name))
        db_team_names = [row[0] for row in result.fetchall()]
        available_teams = list(set(all_team_names + db_team_names))
        logger.info(f"Phase 3: {len(available_teams)} teams available for LLM matching")
        
        processed = 0
        
        # Step 2: Analyze ending nodes (what did they become?)
        logger.info(f"Phase 3: Analyzing {len(ending_nodes)} ending nodes")
        for node in ending_nodes:
            if self._monitor:
                await self._monitor.check_status()
            
            logger.info(f"  Analyzing ending: {node['name']}")
            # For ending nodes (e.g., year=2025), the event (merge/transfer) effectively
            # happens at the start of the NEXT season (2026).
            events = await self._extractor.analyze_ending_node(
                node, 
                available_teams=available_teams,
                event_year_override=node['year'] + 1
            )
            
            if events:
                logger.info(f"    Found {len(events)} lineage event(s)")
                for event in events:
                    logger.info(f"      - {event.get('event_type')}: {event.get('target_name')} (conf: {event.get('confidence')})")
                    # Note: analyze_ending_node now handles calling create_lineage_record
                    # with the correct override passed down.
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
            # For starting nodes (e.g., year=2026), the event happens in that year.
            events = await self._extractor.analyze_starting_node(
                node, 
                available_teams=available_teams,
                event_year_override=node['year']
            )
            
            if events:
                logger.info(f"    Found {len(events)} lineage event(s)")
                for event in events:
                    logger.info(f"      - {event.get('event_type')}: {event.get('target_name')} (conf: {event.get('confidence')})")
                    # Note: analyze_starting_node now handles calling create_lineage_record
            else:
                logger.info(f"    No lineage events detected by LLM")
            
            processed += 1
            await self._session.commit()
        
        logger.info(f"Phase 3: Complete. Analyzed {processed} boundary nodes.")
