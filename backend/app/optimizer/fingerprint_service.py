"""
Fingerprint service for detecting when precomputed layouts become stale.

Generates structural fingerprints of team families that capture only the
data that affects layout (node IDs, years, links) and ignores metadata
like team names.
"""
import hashlib
import json
from typing import Dict, List, Any, Optional


def generate_family_fingerprint(
    family: Dict[str, Any],
    links: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate a structural fingerprint of a family.
    
    The fingerprint captures:
    - Node IDs (sorted for determinism)
    - Link IDs (sorted for determinism)
    - Node years (founding and dissolution)
    - Link years (connection times)
    
    Metadata like team names is intentionally excluded.
    
    Args:
        family: Family data with 'chains' list
        links: List of link/lineage event objects
    
    Returns:
        Fingerprint dict with node_ids, link_ids, node_years, link_years
    """
    chains = family.get("chains", [])
    
    # Extract and sort node IDs
    node_ids = sorted([chain["id"] for chain in chains])
    
    # Extract and sort link IDs
    link_ids = sorted([link["id"] for link in links])
    
    # Build node years map
    node_years = {}
    for chain in chains:
        node_years[chain["id"]] = {
            "founding": chain.get("founding_year"),
            "dissolution": chain.get("dissolution_year")
        }
    
    # Build link years map
    link_years = {}
    for link in links:
        link_years[link["id"]] = link.get("time")
    
    return {
        "node_ids": node_ids,
        "link_ids": link_ids,
        "node_years": node_years,
        "link_years": link_years
    }


def compute_family_hash(fingerprint: Dict[str, Any]) -> str:
    """
    Compute SHA-256 hash of a fingerprint for quick lookup.
    
    Args:
        fingerprint: Fingerprint dict from generate_family_fingerprint
    
    Returns:
        64-character hex string (SHA-256 hash)
    """
    # Convert to JSON with sorted keys for determinism
    fingerprint_json = json.dumps(fingerprint, sort_keys=True)
    
    # Compute SHA-256 hash
    hash_obj = hashlib.sha256(fingerprint_json.encode('utf-8'))
    return hash_obj.hexdigest()
