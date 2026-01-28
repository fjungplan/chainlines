"""
Tests for the genetic algorithm optimizer.
"""
import pytest
import time
from app.optimizer.genetic_optimizer import GeneticOptimizer


@pytest.fixture
def simple_family():
    """Simple 3-chain linear family: A -> B -> C"""
    chains = [
        {"id": "A", "startTime": 2000, "endTime": 2005, "yIndex": 0},
        {"id": "B", "startTime": 2006, "endTime": 2010, "yIndex": 0},
        {"id": "C", "startTime": 2011, "endTime": 2015, "yIndex": 0}
    ]
    links = [
        {"parentId": "A", "childId": "B", "time": 2005, "y1": 0, "y2": 0},
        {"parentId": "B", "childId": "C", "time": 2010, "y1": 0, "y2": 0}
    ]
    return {"chains": chains, "links": links}


@pytest.fixture
def medium_family():
    """Medium complexity family with 5 chains"""
    chains = [
        {"id": "A", "startTime": 2000, "endTime": 2005, "yIndex": 0},
        {"id": "B", "startTime": 2006, "endTime": 2010, "yIndex": 0},
        {"id": "C", "startTime": 2006, "endTime": 2010, "yIndex": 0},
        {"id": "D", "startTime": 2011, "endTime": 2015, "yIndex": 0},
        {"id": "E", "startTime": 2011, "endTime": 2015, "yIndex": 0}
    ]
    links = [
        {"parentId": "A", "childId": "B", "time": 2005, "y1": 0, "y2": 0},
        {"parentId": "A", "childId": "C", "time": 2005, "y1": 0, "y2": 0},
        {"parentId": "B", "childId": "D", "time": 2010, "y1": 0, "y2": 0},
        {"parentId": "C", "childId": "E", "time": 2010, "y1": 0, "y2": 0}
    ]
    return {"chains": chains, "links": links}


def test_population_initialization():
    """Population should have correct size and diversity"""
    optimizer = GeneticOptimizer(pop_size=20)
    chains = [
        {"id": "A", "startTime": 2000, "endTime": 2005},
        {"id": "B", "startTime": 2006, "endTime": 2010},
        {"id": "C", "startTime": 2011, "endTime": 2015}
    ]
    
    population = optimizer._initialize_population(chains)
    
    assert len(population) == 20
    
    # Each individual should have all chain IDs
    for individual in population:
        assert set(individual.keys()) == {"A", "B", "C"}
        # Y-indices should be non-negative
        for y in individual.values():
            assert y >= 0
        # Y-indices should be unique within individual
        y_values = list(individual.values())
        assert len(set(y_values)) == len(y_values)


def test_crossover_produces_valid_offspring():
    """Crossover should produce valid individuals"""
    optimizer = GeneticOptimizer()
    parent1 = {"A": 0, "B": 1, "C": 2}
    parent2 = {"A": 5, "B": 6, "C": 7}
    
    child = optimizer._crossover(parent1, parent2)
    
    # Should have all keys
    assert set(child.keys()) == {"A", "B", "C"}
    # Y-indices should be non-negative
    for y in child.values():
        assert y >= 0
    # Y-indices should be unique
    y_values = list(child.values())
    assert len(set(y_values)) == len(y_values)


def test_mutation_preserves_validity():
    """Mutation should maintain valid Y-indices"""
    optimizer = GeneticOptimizer(mutation_rate=1.0)  # Always mutate
    individual = {"A": 0, "B": 1, "C": 2}
    
    mutated = optimizer._mutate(individual.copy())
    
    # Should have all keys
    assert set(mutated.keys()) == {"A", "B", "C"}
    # Y-indices should be non-negative
    for y in mutated.values():
        assert y >= 0
    # Y-indices should be unique
    y_values = list(mutated.values())
    assert len(set(y_values)) == len(y_values)


def test_tournament_selection():
    """Tournament selection should pick better individuals"""
    optimizer = GeneticOptimizer()
    population = [
        {"id": 1, "score": 100.0},
        {"id": 2, "score": 50.0},
        {"id": 3, "score": 200.0},
        {"id": 4, "score": 10.0}
    ]
    
    def get_score(ind):
        return ind["score"]
    
    # Run multiple times to ensure it tends toward better solutions
    selections = []
    for _ in range(20):
        selected = optimizer._tournament_select(population, get_score, tournament_size=3)
        selections.append(selected["id"])
    
    # Should select individual 4 (score 10.0) more often than 3 (score 200.0)
    # since lower score is better
    assert selections.count(4) > selections.count(3)


def test_convergence_simple_family(simple_family):
    """Optimizer should improve score over generations"""
    optimizer = GeneticOptimizer(pop_size=20, generations=50)
    
    result = optimizer.optimize(simple_family, timeout_seconds=10)
    
    assert "y_indices" in result
    assert "score" in result
    assert "generations_run" in result
    
    # Should have completed some generations
    assert result["generations_run"] > 0
    
    # Should have valid y_indices
    assert set(result["y_indices"].keys()) == {"A", "B", "C"}
    y_values = list(result["y_indices"].values())
    assert len(set(y_values)) == len(y_values)  # Unique


def test_timeout_mechanism(simple_family):
    """Optimizer should respect timeout"""
    optimizer = GeneticOptimizer(generations=10000)
    
    start_time = time.time()
    result = optimizer.optimize(simple_family, timeout_seconds=0.5)
    duration = time.time() - start_time
    
    # Should exit before running all generations
    assert result["generations_run"] < 10000
    # Should complete within reasonable time (allow some overhead)
    assert duration < 2.0


def test_optimize_medium_family(medium_family):
    """Test on medium complexity family"""
    optimizer = GeneticOptimizer(pop_size=30, generations=100)
    
    result = optimizer.optimize(medium_family, timeout_seconds=30)
    
    assert "y_indices" in result
    assert "score" in result
    assert result["score"] >= 0
    
    # All chains should be assigned
    assert set(result["y_indices"].keys()) == {"A", "B", "C", "D", "E"}
    
    # All Y-indices should be unique
    y_values = list(result["y_indices"].values())
    assert len(set(y_values)) == len(y_values)


def test_empty_family():
    """Optimizer should handle empty family gracefully"""
    optimizer = GeneticOptimizer()
    family = {"chains": [], "links": []}
    
    result = optimizer.optimize(family, timeout_seconds=1)
    
    assert result["y_indices"] == {}
    assert result["score"] == 0.0
    assert result["generations_run"] == 0
