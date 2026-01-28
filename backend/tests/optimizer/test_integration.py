"""
Integration tests for the optimizer.
Tests with realistic, larger families.
"""
import pytest
from app.optimizer.genetic_optimizer import GeneticOptimizer


@pytest.fixture
def large_family():
    """Larger family with 15 chains"""
    chains = [
        {"id": f"chain_{i}", "startTime": 2000 + i * 2, "endTime": 2005 + i * 2, "yIndex": 0}
        for i in range(15)
    ]
    
    # Build a tree structure: chain_0 -> chain_1, chain_2
    #                         chain_1 -> chain_3, chain_4
    #                         chain_2 -> chain_5, chain_6
    # etc.
    links = []
    link_id = 0
    for i in range(7):
        left_child = 2 * i + 1
        right_child = 2 * i + 2
        if left_child < 15:
            links.append({
                "parentId": f"chain_{i}",
                "childId": f"chain_{left_child}",
                "time": 2005 + i * 2,
                "y1": 0,
                "y2": 0
            })
        if right_child < 15:
            links.append({
                "parentId": f"chain_{i}",
                "childId": f"chain_{right_child}",
                "time": 2005 + i * 2,
                "y1": 0,
                "y2": 0
            })
    
    return {"chains": chains, "links": links}


@pytest.mark.slow
def test_optimize_large_family(large_family):
    """Test optimization on a larger family (15 nodes)"""
    optimizer = GeneticOptimizer(pop_size=50, generations=200)
    
    result = optimizer.optimize(large_family, timeout_seconds=60)
    
    # Should complete
    assert "y_indices" in result
    assert "score" in result
    assert "generations_run" in result
    
    # Should have assigned all chains
    assert len(result["y_indices"]) == 15
    
    # Should have unique Y-indices
    y_values = list(result["y_indices"].values())
    assert len(set(y_values)) == len(y_values)
    
    # Score should be finite
    assert result["score"] >= 0
    assert result["score"] != float('inf')


def test_score_improvement():
    """Verify that optimization improves score and resolves collisions"""
    chains = [
        {"id": "A", "startTime": 2000, "endTime": 2005, "yIndex": 0},
        {"id": "B", "startTime": 2006, "endTime": 2010, "yIndex": 0},
        {"id": "C", "startTime": 2006, "endTime": 2010, "yIndex": 0},
        {"id": "D", "startTime": 2011, "endTime": 2015, "yIndex": 0},
    ]
    links = [
        {"parentId": "A", "childId": "B", "time": 2005, "y1": 0, "y2": 0},
        {"parentId": "A", "childId": "C", "time": 2005, "y1": 0, "y2": 0},
        {"parentId": "B", "childId": "D", "time": 2010, "y1": 0, "y2": 0},
    ]
    family = {"chains": chains, "links": links}
    
    # Run optimizer with sufficient generations to find solution
    # Use fixed seed for deterministic testing
    import random
    random.seed(42)
    
    optimizer = GeneticOptimizer(pop_size=50, generations=50)
    result = optimizer.optimize(family, timeout_seconds=10)
    
    # 1. Check for collision resolution
    # B and C exist at the same time, so they MUST be on different lanes
    assert result["y_indices"]["B"] != result["y_indices"]["C"]
    
    # 2. Check for reasonable score
    # A heavy collision or crossing usually costs > 5000 (actually typically >10k for cuts)
    # A symmetric star layout (A=0, B=1, C=-1) costs exactly 4000.0
    # So we accept anything < 6000 as a valid, non-colliding solution
    assert result["score"] < 6000


def test_deterministic_with_seed():
    """Same seed should produce same result"""
    chains = [
        {"id": f"chain_{i}", "startTime": 2000 + i, "endTime": 2005 + i, "yIndex": 0}
        for i in range(5)
    ]
    links = [
        {"parentId": f"chain_{i}", "childId": f"chain_{i+1}", "time": 2005 + i, "y1": 0, "y2": 0}
        for i in range(4)
    ]
    family = {"chains": chains, "links": links}
    
    # Run twice with same seed
    import random
    
    random.seed(42)
    optimizer1 = GeneticOptimizer(pop_size=10, generations=20)
    result1 = optimizer1.optimize(family, timeout_seconds=5)
    
    random.seed(42)
    optimizer2 = GeneticOptimizer(pop_size=10, generations=20)
    result2 = optimizer2.optimize(family, timeout_seconds=5)
    
    # Results should match
    assert result1["y_indices"] == result2["y_indices"]
    assert result1["score"] == result2["score"]
