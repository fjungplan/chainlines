"""
Tests for the fingerprint service.
Verifies that fingerprints correctly capture family structure and detect changes.
"""
import pytest
from app.optimizer.fingerprint_service import generate_family_fingerprint, compute_family_hash


def test_fingerprint_generation_structure():
    """Fingerprint should have correct structure"""
    family = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2000, "dissolution_year": 2010},
            {"id": "uuid-2", "founding_year": 2005, "dissolution_year": None}
        ]
    }
    links = [
        {"id": "link-1", "time": 2005, "parentId": "uuid-1", "childId": "uuid-2"}
    ]
    
    fingerprint = generate_family_fingerprint(family, links)
    
    assert "node_ids" in fingerprint
    assert "link_ids" in fingerprint
    assert "node_years" in fingerprint
    assert "link_years" in fingerprint
    
    # Node IDs should be sorted
    assert fingerprint["node_ids"] == ["uuid-1", "uuid-2"]
    
    # Link IDs should be sorted
    assert fingerprint["link_ids"] == ["link-1"]
    
    # Node years should capture founding and dissolution
    assert fingerprint["node_years"]["uuid-1"] == {"founding": 2000, "dissolution": 2010}
    assert fingerprint["node_years"]["uuid-2"] == {"founding": 2005, "dissolution": None}
    
    # Link years should capture time
    assert fingerprint["link_years"]["link-1"] == 2005


def test_fingerprint_changes_on_founding_year_change():
    """Fingerprint should change when founding year changes"""
    family_v1 = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2000, "dissolution_year": 2010}
        ]
    }
    family_v2 = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2001, "dissolution_year": 2010}
        ]
    }
    
    fp1 = generate_family_fingerprint(family_v1, [])
    fp2 = generate_family_fingerprint(family_v2, [])
    
    hash1 = compute_family_hash(fp1)
    hash2 = compute_family_hash(fp2)
    
    assert hash1 != hash2


def test_fingerprint_changes_on_dissolution_year_change():
    """Fingerprint should change when dissolution year changes"""
    family_v1 = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2000, "dissolution_year": 2010}
        ]
    }
    family_v2 = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2000, "dissolution_year": 2011}
        ]
    }
    
    fp1 = generate_family_fingerprint(family_v1, [])
    fp2 = generate_family_fingerprint(family_v2, [])
    
    hash1 = compute_family_hash(fp1)
    hash2 = compute_family_hash(fp2)
    
    assert hash1 != hash2


def test_fingerprint_changes_on_link_added():
    """Fingerprint should change when link is added"""
    family = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2000, "dissolution_year": 2010},
            {"id": "uuid-2", "founding_year": 2005, "dissolution_year": None}
        ]
    }
    
    links_v1 = []
    links_v2 = [
        {"id": "link-1", "time": 2005, "parentId": "uuid-1", "childId": "uuid-2"}
    ]
    
    fp1 = generate_family_fingerprint(family, links_v1)
    fp2 = generate_family_fingerprint(family, links_v2)
    
    hash1 = compute_family_hash(fp1)
    hash2 = compute_family_hash(fp2)
    
    assert hash1 != hash2


def test_fingerprint_stable_on_metadata_change():
    """Fingerprint should NOT change when only metadata changes"""
    # In reality, we'd pass team objects with names, but fingerprint
    # should only look at structural data (IDs and years)
    family_v1 = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2000, "dissolution_year": 2010, "name": "Team A"}
        ]
    }
    family_v2 = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2000, "dissolution_year": 2010, "name": "Team A Renamed"}
        ]
    }
    
    fp1 = generate_family_fingerprint(family_v1, [])
    fp2 = generate_family_fingerprint(family_v2, [])
    
    hash1 = compute_family_hash(fp1)
    hash2 = compute_family_hash(fp2)
    
    # Hashes should be identical since structural data is the same
    assert hash1 == hash2


def test_fingerprint_changes_on_node_added():
    """Fingerprint should change when node is added to family"""
    family_v1 = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2000, "dissolution_year": 2010}
        ]
    }
    family_v2 = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2000, "dissolution_year": 2010},
            {"id": "uuid-2", "founding_year": 2005, "dissolution_year": None}
        ]
    }
    
    fp1 = generate_family_fingerprint(family_v1, [])
    fp2 = generate_family_fingerprint(family_v2, [])
    
    hash1 = compute_family_hash(fp1)
    hash2 = compute_family_hash(fp2)
    
    assert hash1 != hash2


def test_compute_family_hash_deterministic():
    """Same fingerprint should produce same hash"""
    family = {
        "chains": [
            {"id": "uuid-1", "founding_year": 2000, "dissolution_year": 2010},
            {"id": "uuid-2", "founding_year": 2005, "dissolution_year": None}
        ]
    }
    links = [
        {"id": "link-1", "time": 2005, "parentId": "uuid-1", "childId": "uuid-2"}
    ]
    
    fp1 = generate_family_fingerprint(family, links)
    fp2 = generate_family_fingerprint(family, links)
    
    hash1 = compute_family_hash(fp1)
    hash2 = compute_family_hash(fp2)
    
    assert hash1 == hash2
    # Hash should be 64 characters (SHA-256 hex)
    assert len(hash1) == 64
