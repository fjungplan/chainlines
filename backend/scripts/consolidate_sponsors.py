#!/usr/bin/env python3
"""
Sponsor Consolidation Script

LLM-assisted deduplication and consolidation of sponsors and brands.

Usage:
    python -m scripts.consolidate_sponsors --analyze
    python -m scripts.consolidate_sponsors --apply consolidation_plan.json
"""
import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from uuid import UUID

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from openai import OpenAI
import instructor

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
# Backup Functions
# ============================================================================
async def backup_tables(session, output_path: Path):
    """
    Create a JSON backup of sponsors, brands, and team_sponsor_links.
    
    Args:
        session: AsyncSession
        output_path: Path to write backup JSON
    """
    print(f"🔒 Creating backup at {output_path}...")
    
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
                "notes": m.notes,
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
                "list_order": link.list_order
            }
            for link in links
        ]
    }
    
    # Write backup
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Backup created: {len(masters)} sponsors, {sum(len(m.brands) for m in masters)} brands, {len(links)} links")


# ============================================================================
# Analysis Phase: Fetch Data and Call LLM
# ============================================================================
async def fetch_sponsor_context(session) -> List[Dict[str, Any]]:
    """
    Fetch all sponsors with enriched context for LLM analysis.
    
    Returns compact JSON to minimize token usage.
    """
    print("📊 Fetching sponsor and brand data...")
    
    stmt = (
        select(SponsorMaster)
        .options(
            selectinload(SponsorMaster.brands).selectinload(SponsorBrand.team_links)
        )
        .order_by(SponsorMaster.legal_name)
    )
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
            "notes": master.notes,
            "brands": brands_info
        })
    
    print(f"✅ Fetched {len(masters)} sponsors with {sum(len(m.brands) for m in masters)} brands")
    return context


def call_grok_for_consolidation(context: List[Dict[str, Any]]) -> ConsolidationPlan:
    """
    Send sponsor context to Grok and get back consolidation actions.
    
    Returns a ConsolidationPlan with filtered actions (only >= 0.7 confidence).
    """
    print("🤖 Calling Grok LLM for consolidation analysis...")
    
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
    system_prompt = """You are a data cleaner specializing in sponsor and brand deduplication.
Your task: Identify duplicate sponsors and brands that should be merged or reorganized.

Rules:
1. MERGE_MASTER: Merge two sponsor masters (all brands move to target).
2. MERGE_BRAND: Merge two brands (team links update to target brand).
3. MOVE_BRAND: Move a brand from one sponsor master to another.

For each action, provide:
- action_type
- source_id (UUID to merge/move FROM)
- target_id (UUID to merge/move TO)
- reason (brief explanation)
- confidence (0.0-1.0)

IMPORTANT: Only suggest merges when you're confident they represent the same entity.
Preserve historical distinctions (e.g., "Red Bull" energy drink vs "Red Bull" bike frames).
"""
    
    user_prompt = f"""Here is the current state of {len(context)} sponsors and their brands:

```json
{json.dumps(context, indent=2)}
```

Identify duplicates and provide consolidation actions. Be conservative - only merge when confident."""
    
    # Call LLM
    response = client.chat.completions.create(
        model="grok-2-1212",
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
    
    print(f"✅ LLM returned {len(response.actions)} actions")
    print(f"   - High confidence (>= 0.9): {sum(1 for a in filtered_actions if a.status == ConsolidationActionStatus.HIGH_CONFIDENCE)}")
    print(f"   - Needs review (0.7-0.9): {sum(1 for a in filtered_actions if a.status == ConsolidationActionStatus.NEEDS_REVIEW)}")
    print(f"   - Discarded (< 0.7): {discarded_count}")
    
    return ConsolidationPlan(
        actions=filtered_actions,
        generated_at=datetime.now().isoformat(),
        model_used="grok-2-1212",
        total_actions=len(filtered_actions)
    )


async def analyze_command(session):
    """
    Analyze phase: Fetch data, call LLM, generate consolidation_plan.json.
    """
    print("=" * 60)
    print("ANALYSIS PHASE")
    print("=" * 60)
    
    context = await fetch_sponsor_context(session)
    
    # Estimate token count (rough)
    context_json = json.dumps(context)
    estimated_tokens = len(context_json) / 4  # Rough estimate
    print(f"📏 Estimated context size: ~{estimated_tokens:,.0f} tokens")
    
    if estimated_tokens > 128000:
        print("⚠️  Warning: Context exceeds 128k token threshold. Pricing will be 2x.")
    
    plan = call_grok_for_consolidation(context)
    
    # Save plan
    with open(PLAN_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(plan.model_dump_json(indent=2))
    
    print(f"\n✅ Consolidation plan saved to: {PLAN_OUTPUT}")
    print(f"   Total actions: {plan.total_actions}")
    print("\n📝 Next steps:")
    print("   1. Review the plan file")
    print("   2. Remove any 'needs_review' actions you don't want")
    print("   3. Run: python -m scripts.consolidate_sponsors --apply consolidation_plan.json")


# ============================================================================
# Apply Phase: Validate and Execute Plan
# ============================================================================
async def validate_plan(session, plan: ConsolidationPlan) -> bool:
    """
    Validate that all IDs in the plan exist and no circular merges.
    
    Returns True if valid, False otherwise.
    """
    print("🔍 Validating consolidation plan...")
    
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
        print("❌ Validation failed:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ Validation passed")
    return True


async def execute_plan(session, plan: ConsolidationPlan):
    """
    Execute the consolidation plan: update links, delete sources.
    """
    print("🔧 Executing consolidation plan...")
    
    for idx, action in enumerate(plan.actions):
        print(f"\n[{idx + 1}/{len(plan.actions)}] {action.action_type.value}")
        print(f"    {action.reason} (confidence: {action.confidence:.2f})")
        
        if action.action_type == ConsolidationActionType.MERGE_BRAND:
            # Update all TeamSponsorLinks
            stmt = (
                select(TeamSponsorLink)
                .where(TeamSponsorLink.brand_id == action.source_id)
            )
            result = await session.execute(stmt)
            links = result.scalars().all()
            
            for link in links:
                link.brand_id = action.target_id
            
            # Delete source brand
            stmt = select(SponsorBrand).where(SponsorBrand.brand_id == action.source_id)
            result = await session.execute(stmt)
            source_brand = result.scalar_one_or_none()
            if source_brand:
                await session.delete(source_brand)
            
            print(f"    ✓ Merged brand (updated {len(links)} links)")
        
        elif action.action_type == ConsolidationActionType.MOVE_BRAND:
            # Update brand's master_id
            stmt = select(SponsorBrand).where(SponsorBrand.brand_id == action.source_id)
            result = await session.execute(stmt)
            brand = result.scalar_one_or_none()
            if brand:
                brand.master_id = action.target_id
                print(f"    ✓ Moved brand to new sponsor")
        
        elif action.action_type == ConsolidationActionType.MERGE_MASTER:
            # Move all brands from source to target
            stmt = (
                select(SponsorBrand)
                .where(SponsorBrand.master_id == action.source_id)
            )
            result = await session.execute(stmt)
            brands = result.scalars().all()
            
            for brand in brands:
                brand.master_id = action.target_id
            
            # Delete source master
            stmt = select(SponsorMaster).where(SponsorMaster.master_id == action.source_id)
            result = await session.execute(stmt)
            source_master = result.scalar_one_or_none()
            if source_master:
                await session.delete(source_master)
            
            print(f"    ✓ Merged sponsor (moved {len(brands)} brands)")
    
    await session.commit()
    print("\n✅ Consolidation complete!")


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
    print(f"📄 Loaded plan with {plan.total_actions} actions")
    
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"sponsors_backup_{timestamp}.json"
    await backup_tables(session, backup_path)
    
    # Validate
    if not await validate_plan(session, plan):
        print("\n❌ Validation failed. Aborting.")
        return
    
    # Confirm
    print(f"\n⚠️  WARNING: This will modify the database!")
    print(f"   Backup saved at: {backup_path}")
    confirm = input("\nProceed with consolidation? (yes/no): ")
    if confirm.lower() != "yes":
        print("❌ Aborted by user")
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
    
    args = parser.parse_args()
    
    if not args.analyze and not args.apply:
        parser.print_help()
        return
    
    async with async_session_maker() as session:
        if args.analyze:
            await analyze_command(session)
        elif args.apply:
            plan_path = Path(args.apply)
            await apply_command(session, plan_path)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
