
import pytest
from app.optimizer.genetic_optimizer import GeneticOptimizer

@pytest.fixture
def simple_family():
    chains = [
        {"id": "A", "startTime": 2000, "endTime": 2005, "yIndex": 0},
        {"id": "B", "startTime": 2006, "endTime": 2010, "yIndex": 0},
    ]
    links = [
        {"parentId": "A", "childId": "B", "time": 2005, "y1": 0, "y2": 0},
    ]
    return {"chains": chains, "links": links}

def test_genetic_optimizer_detailed_stats(simple_family):
    """Verify that optimize() returns detailed stats including cost breakdown."""
    optimizer = GeneticOptimizer(pop_size=10, generations=20)
    
    result = optimizer.optimize(simple_family)
    
    assert "best_generation" in result
    assert "total_generations" in result
    assert "lane_count" in result
    assert "cost_breakdown" in result
    
    breakdown = result["cost_breakdown"]
    assert "ATTRACTION" in breakdown
    assert "multiplier" in breakdown["ATTRACTION"]
    assert "sum" in breakdown["ATTRACTION"]
    
    # Check valid values
    assert result["total_generations"] >= result["best_generation"]
    assert result["lane_count"] >= 1
    assert result["score"] >= 0
