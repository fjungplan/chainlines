#!/usr/bin/env python3
"""
Sponsor Consolidation Script

LLM-assisted deduplication and consolidation of sponsors and brands.

"""
import os
import sys
import re
import unicodedata
import argparse
import json
import difflib
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# PATCH: If running locally on Windows, 'postgres' hostname won't resolve.
# We need to replace it with 'localhost' for the script to work from host.
if os.getenv("DATABASE_URL") and "@postgres" in os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL").replace("@postgres", "@localhost")
    print(f"[NOTE] Patched DATABASE_URL for local execution: {os.environ['DATABASE_URL'].split('@')[-1]}")

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import instructor
from openai import OpenAI

from app.db.database import async_session_maker
from app.models.sponsor import SponsorMaster, SponsorBrand, TeamSponsorLink
from app.schemas.consolidation import (
    ConsolidationPlan,
    ConsolidationAction,
    ConsolidationActionType,
    ConsolidationActionStatus
)

# ============================================================================
# Constants
# ============================================================================
CONFIDENCE_HIGH = 0.9
CONFIDENCE_REVIEW = 0.7
BACKUP_DIR = Path(__file__).parent.parent / "backups"
PLAN_OUTPUT = Path(__file__).parent.parent / "consolidation_plan.json"

# ============================================================================
# Smart Clustering Logic
# ============================================================================
def normalize_str(s):
    if not s: return ""
    # Normalize unicode (strip accents) and lowercase, keep alphanumeric
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'[^a-z0-9]', '', s.lower())

def cluster_sponsors(sponsors: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    Group sponsors into clusters based on fuzzy matching of their names and brands.
    Uses a graph connected components approach.
    """
    print("[CLUSTER] Starting smart fuzzy clustering...")
    
    # 1. Extract all unique terms (names and brand names)
    # Map term -> list of sponsor_ids that use it
    term_to_sponsors = defaultdict(list)
    unique_terms = set()
    
    for s in sponsors:
        terms = []
        # Add sponsor name
        if s.get("n"): terms.append(normalize_str(s["n"]))
        # Add brand names
        for b in s.get("brands", []):
            if b.get("n"): terms.append(normalize_str(b["n"]))
            
        for term in set(terms): # Dedup within sponsor
            if len(term) > 3: # Skip very short terms to avoid noise
                term_to_sponsors[term].append(s["id"])
                unique_terms.add(term)
    
    unique_terms_list = sorted(list(unique_terms))
    print(f"[CLUSTER] Found {len(unique_terms_list)} unique terms to cluster")
    
    # 2. Cluster terms using fuzzy matching (Greedy O(N^2) but N is limited)
    # term_clusters maps term -> cluster_id
    term_clusters = {}
    cluster_counter = 0
    
    # Optimization: Sort by length/alpha to speed up
    # We'll simpler greedy approach:
    # Taking a set of unvisited terms
    unvisited = set(unique_terms_list)
    
    print("[CLUSTER] Computing fuzzy matches (this might take a moment)...")
    progress = 0
    total = len(unvisited)
    
    while unvisited:
        # Pick a seed term
        seed = unvisited.pop()
        current_cluster_id = cluster_counter
        term_clusters[seed] = current_cluster_id
        
        # Find all similar terms in remaining unvisited
        # Using list(unvisited) to avoid runtime modification issues
        candidates = list(unvisited) 
        
        # Heuristic: only check candidates with length within +/- 30%
        seed_len = len(seed)
        min_len = int(seed_len * 0.7)
        max_len = int(seed_len * 1.3)
        
        for candidate in candidates:
            if not (min_len <= len(candidate) <= max_len):
                continue
                
            # Quick check: disjoint letters?
            if set(seed).isdisjoint(set(candidate)):
                continue
                
            # Deep check
            ratio = difflib.SequenceMatcher(None, seed, candidate).ratio()
            if ratio > 0.85: # High similarity threshold
                term_clusters[candidate] = current_cluster_id
                unvisited.remove(candidate)
        
        cluster_counter += 1
        
        progress += 1
        if progress % 500 == 0:
            print(f"   ... clustered {progress} groups")

    print(f"[CLUSTER] Identified {cluster_counter} distinct semantic term groups")

    # 3. Build Adjacency Graph of Sponsors
    # Nodes: Sponsor IDs
    # Edges: If two sponsors share a term OR have terms in the same cluster
    
    sponsor_adj = defaultdict(set)
    sponsor_map = {s["id"]: s for s in sponsors}
    all_sponsor_ids = list(sponsor_map.keys())
    
    # Invert mapping: Cluster ID -> List of Sponsors
    cluster_to_sponsors = defaultdict(set)
    
    for term, s_ids in term_to_sponsors.items():
        if term in term_clusters:
            c_id = term_clusters[term]
            for s_id in s_ids:
                cluster_to_sponsors[c_id].add(s_id)
                
    # Create edges for all sponsors in the same cluster
    for c_id, s_ids in cluster_to_sponsors.items():
        s_ids_list = list(s_ids)
        for i in range(len(s_ids_list)):
            for j in range(i + 1, len(s_ids_list)):
                u, v = s_ids_list[i], s_ids_list[j]
                sponsor_adj[u].add(v)
                sponsor_adj[v].add(u)
                
    # 4. Find Connected Components (The "Mega Chunks")
    visited = set()
    final_groups = []
    
    for s_id in all_sponsor_ids:
        if s_id in visited:
            continue
            
        # BFS to find component
        component = []
        queue = [s_id]
        visited.add(s_id)
        
        while queue:
            node = queue.pop(0)
            component.append(sponsor_map[node])
            
            for neighbor in sponsor_adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    
        final_groups.append(component)
        
    print(f"[CLUSTER] Grouped {len(all_sponsor_ids)} sponsors into {len(final_groups)} connected clusters")
    
    # Sort groups by size (largest first purely for interest) and then name
    final_groups.sort(key=lambda g: (-len(g), g[0]["n"]))
    
    return final_groups


async def analyze_command(session, limit: int = None):
    """
    Analyze phase: Fetch data, call LLM, generate consolidation_plan.json.
    """
    print("=" * 60)
    print("ANALYSIS PHASE")
    print("=" * 60)
    
    context = await fetch_sponsor_context(session, limit=limit)
    
    # SMART CLUSTERING
    # Returns list of lists: [[SponsorA, SponsorB], [SponsorC], ...]
    clusters = cluster_sponsors(context)
    
    # Flatten clusters into a single sorted list for chunking
    # But keep clusters adjacent!
    sorted_context = []
    for cluster in clusters:
        sorted_context.extend(cluster)
        
    # Recalculate metrics
    context_json = json.dumps(sorted_context)
    estimated_tokens = len(context_json) / 4
    print(f"[SIZE] Total context size: ~{estimated_tokens:,.0f} tokens")

    # Chunking Strategy
    # We want to preserve clusters. Breaking a cluster across chunks is bad.
    # We greedily build chunks from clusters.
    
    CHUNK_SIZE_LIMIT = 200 # Items per chunk
    
    chunks = []
    current_chunk = []
    
    for cluster in clusters:
        # If adding this cluster exceeds limit roughly, push current chunk
        # (Unless cluster itself is huge, then we have to handle it)
        if len(current_chunk) + len(cluster) > CHUNK_SIZE_LIMIT:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
        
        current_chunk.extend(cluster)
    
    if current_chunk:
        chunks.append(current_chunk)
        
    print(f"[LLM] Prepared {len(chunks)} chunks for processing (respecting cluster boundaries)")
    
    all_actions = []
    
    for i, chunk in enumerate(chunks):
        print(f"\n[LLM] Processing chunk {i+1}/{len(chunks)} ({len(chunk)} sponsors)...")
        # Print sample names to verify clustering
        sample_names = [s["n"] for s in chunk[:3]]
        print(f"      Starts with: {', '.join(sample_names)}...")
        
        try:
            plan = call_grok_for_consolidation(chunk)
            all_actions.extend(plan.actions)
            print(f"   => Found {len(plan.actions)} actions")
        except Exception as e:
            print(f"[ERROR] Failed chunk: {e}")

    # Deduplicate actions
    unique_actions = {}
    for action in all_actions:
        key = f"{action.action_type}:{action.source_id}:{action.target_id}"
        if key not in unique_actions:
            unique_actions[key] = action
    
    print(f"\n[OK] Aggregated {len(unique_actions)} unique actions")
    
    final_actions = list(unique_actions.values())
    
    plan = ConsolidationPlan(
        actions=final_actions,
        generated_at=datetime.now().isoformat(),
        model_used="grok-4-1-fast-reasoning",
        total_actions=len(final_actions)
    )
    
    # Save plan
    with open(PLAN_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(plan.model_dump_json(indent=2))
    
    print(f"\n[OK] Consolidation plan saved to: {PLAN_OUTPUT}")

# Backup Functions
# ============================================================================
async def backup_tables(session, output_path: Path):
    """
    Create a JSON backup of sponsors, brands, and team_sponsor_links.
    
    Args:
        session: AsyncSession
        output_path: Path to write backup JSON
    """
    print(f"[BACKUP] Creating backup at {output_path}...")
    
    # Fetch all sponsors with brands
    stmt = select(SponsorMaster).options(selectinload(SponsorMaster.brands))
    result = await session.execute(stmt)
    masters = result.scalars().all()
    
    # Fetch all links
    stmt = select(TeamSponsorLink)
    result = await session.execute(stmt)
    links = result.scalars().all()
    
    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "sponsors": [
            {
                "master_id": str(m.master_id),
                "legal_name": m.legal_name,
                "industry_sector": m.industry_sector,
                "source_url": m.source_url,
                "source_notes": m.source_notes,
                "brands": [
                    {
                        "brand_id": str(b.brand_id),
                        "brand_name": b.brand_name,
                        "display_name": b.display_name,
                        "default_hex_color": b.default_hex_color
                    }
                    for b in m.brands
                ]
            }
            for m in masters
        ],
        "team_sponsor_links": [
            {
                "link_id": str(link.link_id),
                "era_id": str(link.era_id),
                "brand_id": str(link.brand_id),
                "rank_order": link.rank_order
            }
            for link in links
        ]
    }
    
    # Write backup
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Backup created: {len(masters)} sponsors, {sum(len(m.brands) for m in masters)} brands, {len(links)} links")


# ============================================================================
# Analysis Phase: Fetch Data and Call LLM
# ============================================================================
async def fetch_sponsor_context(session, limit: int = None) -> List[Dict[str, Any]]:
    """
    Fetch all sponsors with enriched context for LLM analysis.
    
    Returns compact JSON to minimize token usage.
    """
    print("[DATA] Fetching sponsor and brand data...")
    
    stmt = (
        select(SponsorMaster)
        .options(
            selectinload(SponsorMaster.brands).selectinload(SponsorBrand.team_links)
        )
        .order_by(SponsorMaster.legal_name)
    )
    
    if limit:
        stmt = stmt.limit(limit)
        
    result = await session.execute(stmt)
    masters = result.scalars().all()
    
    # Build compact context
    context = []
    for master in masters:
        brands_info = []
        for brand in master.brands:
            link_count = len(brand.team_links)
            # Get year range if links exist
            if link_count > 0:
                # Note: We'd need to join TeamEra to get years, but for token efficiency,
                # just use link count for now
                brands_info.append({
                    "id": str(brand.brand_id),
                    "n": brand.brand_name,  # 'n' = name (short key)
                    "dn": brand.display_name,
                    "uses": link_count
                })
            else:
                brands_info.append({
                    "id": str(brand.brand_id),
                    "n": brand.brand_name,
                    "dn": brand.display_name,
                    "uses": 0
                })
        
        context.append({
            "id": str(master.master_id),
            "n": master.legal_name,
            "sector": master.industry_sector,
            "url": master.source_url,
            "notes": master.source_notes,
            "brands": brands_info
        })
    
    print(f"[OK] Fetched {len(masters)} sponsors with {sum(len(m.brands) for m in masters)} brands")
    return context


def call_grok_for_consolidation(context: List[Dict[str, Any]]) -> ConsolidationPlan:
    """
    Send sponsor context to Grok and get back consolidation actions.
    
    Returns a ConsolidationPlan with filtered actions (only >= 0.7 confidence).
    """
    print("[LLM] Calling Grok LLM for consolidation analysis...")
    
    # Initialize Grok client via instructor
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        raise ValueError("GROK_API_KEY not found in environment")
    
    client = instructor.from_openai(
        OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        ),
        mode=instructor.Mode.JSON
    )
    
    # Construct prompt
    system_prompt = """You are a data cleaner specializing in sponsor and brand deduplication for professional cycling teams.

Context: These sponsors and brands are associated with historic and current professional cycling teams. 
Brands represent how sponsors appear on team jerseys and in team names.

Your task: AGGRESSIVELY identify duplicates and reorganize the data.
We prefer fewer, cleaner entities over preserving minor variations.

Rules:
1. MERGE_MASTER: Merge two sponsor masters (all brands move to target).
    - Use this when two Sponsors are the SAME company (e.g. "Stellantis" and "Peugeot" if Peugeot is just a child brand).
    - Merge regional branches into the main company.
2. MERGE_BRAND: Merge two brands (team links update to target brand).
    - Use this for spelling variations (Citroen -> Citroën).
    - Use this for abbreviations (FDJ -> Française des Jeux).
    - MERGE BRANDS WITHIN THE SAME SPONSOR if they are duplicates!
3. MOVE_BRAND: Move a brand from one sponsor master to another.
    - Use this if a brand is listed under the wrong parent.

For each action, provide:
- action_type
- source_id (UUID)
- target_id (UUID)
- reason (brief explanation)
- confidence (0.0-1.0)

GUIDELINES:
- **Synonyms & Abbreviations**: "FDJ" IS "Française des Jeux". "C.A." IS "Crédit Agricole". MERGE THEM.
- **Accents**: "Citroen" IS "Citroën". MERGE THEM.
- **Parent/Child**: If you see a "Peugeot" sponsor and a "Stellantis" sponsor with "Peugeot" brand, consider merging the Peugeot sponsor into Stellantis (or vice versa, whichever seems to be the primary 'Cycling Identity').
  - *Preference*: Keep the name most commonly used in cycling (e.g. "Peugeot" might be preferred over "Stellantis" if "Peugeot" is the historic team name).
- **Consolidate**: If a Sponsor has 3 brands: "FDJ", "F.D.J.", "La Française des Jeux", pick the BEST one (e.g. "Française des Jeux" or "FDJ") and merge the others into it.
"""
    
    user_prompt = f"""Here is the current state of {len(context)} sponsors and their brands:

```json
{json.dumps(context, indent=2)}
```

Identify duplicates and provide consolidation actions. Be conservative - only merge when confident."""
    
    # Call LLM
    response = client.chat.completions.create(
        model="grok-4-1-fast-reasoning",
        response_model=ConsolidationPlan,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=8000
    )
    
    # Filter and classify by confidence
    filtered_actions = []
    discarded_count = 0
    
    for action in response.actions:
        if action.confidence >= CONFIDENCE_HIGH:
            action.status = ConsolidationActionStatus.HIGH_CONFIDENCE
            filtered_actions.append(action)
        elif action.confidence >= CONFIDENCE_REVIEW:
            action.status = ConsolidationActionStatus.NEEDS_REVIEW
            filtered_actions.append(action)
        else:
            # Discard low confidence
            discarded_count += 1
    
    print(f"[OK] LLM returned {len(response.actions)} actions")
    print(f"   - High confidence (>= 0.9): {sum(1 for a in filtered_actions if a.status == ConsolidationActionStatus.HIGH_CONFIDENCE)}")
    print(f"   - Needs review (0.7-0.9): {sum(1 for a in filtered_actions if a.status == ConsolidationActionStatus.NEEDS_REVIEW)}")
    print(f"   - Discarded (< 0.7): {discarded_count}")
    
    return ConsolidationPlan(
        actions=filtered_actions,
        generated_at=datetime.now().isoformat(),
        model_used="grok-4-1-fast-reasoning",
        total_actions=len(filtered_actions)
    )





# ============================================================================
# Apply Phase: Validate and Execute Plan
# ============================================================================
async def validate_plan(session, plan: ConsolidationPlan) -> bool:
    """
    Validate that all IDs in the plan exist and no circular merges.
    
    Returns True if valid, False otherwise.
    """
    print("[CHECK] Validating consolidation plan...")
    
    # Fetch all master and brand IDs
    stmt = select(SponsorMaster.master_id)
    result = await session.execute(stmt)
    master_ids = {row[0] for row in result.fetchall()}
    
    stmt = select(SponsorBrand.brand_id)
    result = await session.execute(stmt)
    brand_ids = {row[0] for row in result.fetchall()}
    
    errors = []
    for idx, action in enumerate(plan.actions):
        # Check IDs exist
        if action.action_type == ConsolidationActionType.MERGE_MASTER:
            if action.source_id not in master_ids:
                errors.append(f"Action {idx}: Source master {action.source_id} not found")
            if action.target_id not in master_ids:
                errors.append(f"Action {idx}: Target master {action.target_id} not found")
        
        elif action.action_type in [ConsolidationActionType.MERGE_BRAND, ConsolidationActionType.MOVE_BRAND]:
            if action.source_id not in brand_ids:
                errors.append(f"Action {idx}: Source brand {action.source_id} not found")
            if action.action_type == ConsolidationActionType.MERGE_BRAND:
                if action.target_id not in brand_ids:
                    errors.append(f"Action {idx}: Target brand {action.target_id} not found")
            else:  # MOVE_BRAND
                if action.target_id not in master_ids:
                    errors.append(f"Action {idx}: Target master {action.target_id} not found")
    
    if errors:
        print("[ERROR] Validation failed:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("[OK] Validation passed")
    return True


async def execute_plan(session, plan: ConsolidationPlan):
    """
    Execute the consolidation plan: update links, delete sources.
    """
    print("[EXEC] Executing consolidation plan...")
    
    for idx, action in enumerate(plan.actions):
        print(f"\n[{idx + 1}/{len(plan.actions)}] {action.action_type.value}")
        print(f"    {action.reason} (confidence: {action.confidence:.2f})")
        
        if action.action_type == ConsolidationActionType.MERGE_BRAND:
            # Check target links for collision to avoid uq_era_brand violation
            stmt_t = select(TeamSponsorLink.era_id).where(TeamSponsorLink.brand_id == action.target_id)
            res_t = await session.execute(stmt_t)
            target_era_ids = set(res_t.scalars().all())

            # Update all TeamSponsorLinks
            stmt = (
                select(TeamSponsorLink)
                .where(TeamSponsorLink.brand_id == action.source_id)
            )
            result = await session.execute(stmt)
            links = result.scalars().all()
            
            updated_count = 0
            for link in links:
                if link.era_id in target_era_ids:
                    # Collision! Target brand already linked to this era. Delete redundant source link.
                    await session.delete(link)
                else:
                    link.brand_id = action.target_id
                    updated_count += 1
            
            # Delete source brand
            stmt = select(SponsorBrand).where(SponsorBrand.brand_id == action.source_id)
            result = await session.execute(stmt)
            source_brand = result.scalar_one_or_none()
            if source_brand:
                await session.delete(source_brand)
            
            print(f"    OK Merged brand (updated {len(links)} links)")
        
        elif action.action_type == ConsolidationActionType.MOVE_BRAND:
            # Update brand's master_id
            stmt = select(SponsorBrand).where(SponsorBrand.brand_id == action.source_id)
            result = await session.execute(stmt)
            brand = result.scalar_one_or_none()
            if brand:
                brand.master_id = action.target_id
                print(f"    OK Moved brand to new sponsor")
        
        elif action.action_type == ConsolidationActionType.MERGE_MASTER:
            # 1. Fetch target's existing brands to check for collisions
            stmt_targets = select(SponsorBrand).where(SponsorBrand.master_id == action.target_id)
            res_t = await session.execute(stmt_targets)
            target_brands_map = {b.brand_name: b for b in res_t.scalars().all()}
            
            # 2. Fetch source brands
            stmt = (
                select(SponsorBrand)
                .where(SponsorBrand.master_id == action.source_id)
            )
            result = await session.execute(stmt)
            source_brands = result.scalars().all()
            
            moved_count = 0
            merged_count = 0
            
            for brand in source_brands:
                if brand.brand_name in target_brands_map:
                    # Collision! Merge into duplicate target brand
                    target_brand = target_brands_map[brand.brand_name]
                    
                    # Move all links from source brand to target brand
                    stmt_links = select(TeamSponsorLink).where(TeamSponsorLink.brand_id == brand.brand_id)
                    links_res = await session.execute(stmt_links)
                    links = links_res.scalars().all()
                    
                    # Check target brand links for collision
                    stmt_t = select(TeamSponsorLink.era_id).where(TeamSponsorLink.brand_id == target_brand.brand_id)
                    res_t = await session.execute(stmt_t)
                    target_era_ids = set(res_t.scalars().all())
                    
                    for link in links:
                        if link.era_id in target_era_ids:
                            # Collision! Delete redundant link
                            await session.delete(link)
                        else:
                            link.brand_id = target_brand.brand_id
                    
                    # Delete the now-empty source brand
                    await session.delete(brand)
                    merged_count += 1
                else:
                    # No collision, just re-parent
                    brand.master_id = action.target_id
                    moved_count += 1
            
            # 3. Delete source master
            stmt = select(SponsorMaster).where(SponsorMaster.master_id == action.source_id)
            result = await session.execute(stmt)
            source_master = result.scalar_one_or_none()
            if source_master:
                await session.delete(source_master)
            
            print(f"    OK Merged sponsor (moved {moved_count}, merged {merged_count} brands)")
    
    await session.commit()
    print("\n[OK] Consolidation complete!")


async def apply_command(session, plan_path: Path):
    """
    Apply phase: Read plan, backup, validate, execute.
    """
    print("=" * 60)
    print("APPLY PHASE")
    print("=" * 60)
    
    # Load plan
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
    
    with open(plan_path, 'r', encoding='utf-8') as f:
        plan_data = json.load(f)
    
    plan = ConsolidationPlan.model_validate(plan_data)
    print(f"[FILE] Loaded plan with {plan.total_actions} actions")
    
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"sponsors_backup_{timestamp}.json"
    await backup_tables(session, backup_path)
    
    # Validate
    if not await validate_plan(session, plan):
        print("\n[ERROR] Validation failed. Aborting.")
        return
    
    # Confirm
    print(f"\n[WARN]  WARNING: This will modify the database!")
    print(f"   Backup saved at: {backup_path}")
    confirm = input("\nProceed with consolidation? (yes/no): ")
    if confirm.lower() != "yes":
        print("[ERROR] Aborted by user")
        return
    
    # Execute
    await execute_plan(session, plan)


# ============================================================================
# Main CLI
# ============================================================================
async def main():
    parser = argparse.ArgumentParser(description="Sponsor Consolidation Script")
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze sponsors/brands and generate consolidation plan"
    )
    parser.add_argument(
        "--apply",
        type=str,
        metavar="PLAN_FILE",
        help="Apply a consolidation plan (provide path to plan JSON)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of sponsors to analyze (for testing)"
    )
    
    args = parser.parse_args()
    
    if not args.analyze and not args.apply:
        parser.print_help()
        return
    
    async with async_session_maker() as session:
        if args.analyze:
            await analyze_command(session, limit=args.limit)
        elif args.apply:
            plan_path = Path(args.apply)
            await apply_command(session, plan_path)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

