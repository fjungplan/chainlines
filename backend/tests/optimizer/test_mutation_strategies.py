"""
Test: Configurable Mutation Strategies

Verifies that mutation strategies can be controlled via configuration
probabilities, removing the need for internal random patching.
"""
import pytest
from app.optimizer.genetic_optimizer import GeneticOptimizer
from unittest.mock import patch

class TestMutationStrategies:
    
    def test_mutate_forces_swap_via_config(self):
        """Verify that setting SWAP=1.0 forces swap mutation."""
        strategies = {"SWAP": 1.0, "HEURISTIC": 0.0, "COMPACTION": 0.0, "EXPLORATION": 0.0}
        optimizer = GeneticOptimizer(mutation_strategies=strategies)
        
        individual = {"A": 10, "B": 20, "C": 30}
        
        # We still patch random.sample for the swap selection itself (which pair to swap)
        # BUT we don't handle the strategy selection logic via patch anymore
        with patch('random.sample', return_value=["A", "B"]):
             # We rely on optimizer to PICK swap strategy due to 1.0 probability
             # We assume random.random() calls for mutation rate check > 0.0 pass
             # We need to ensure mutation_rate check passes. 
             # optimizer default mutation rate is 0.1, random.random() needs to be < 0.1
             # We can force mutation_rate=1.0 in init
             
             optimizer.mutation_rate = 1.0
             mutated = optimizer._mutate(individual.copy())
        
        # A should be 20, B should be 10 (Swap occurred)
        assert mutated["A"] == 20
        assert mutated["B"] == 10
        
    def test_mutate_forces_heuristic_via_config(self):
        """Verify that setting HEURISTIC=1.0 forces heuristic mutation."""
        strategies = {"SWAP": 0.0, "HEURISTIC": 1.0, "COMPACTION": 0.0, "EXPLORATION": 0.0}
        optimizer = GeneticOptimizer(mutation_strategies=strategies)
        optimizer.mutation_rate = 1.0
        
        individual = {"Child": 50, "Parent": 10}
        chain_parents = {"Child": [{"id": "Parent"}]}
        chain_children = {"Parent": [{"id": "Child"}]}
        
        # We still need to patch random.choice for the Heuristic target selection
        with patch('random.choice') as mock_choice:
            mock_choice.side_effect = ["Child", {"id": "Parent"}]
            
            mutated = optimizer._mutate(
                individual.copy(), 
                chain_parents=chain_parents, 
                chain_children=chain_children
            )
            
        assert mutated["Child"] == 10
        
    def test_mutate_forces_compaction_via_config(self):
        """Verify that setting COMPACTION=1.0 forces move to used lane."""
        strategies = {"SWAP": 0.0, "HEURISTIC": 0.0, "COMPACTION": 1.0, "EXPLORATION": 0.0}
        optimizer = GeneticOptimizer(mutation_strategies=strategies)
        optimizer.mutation_rate = 1.0
        
        individual = {"A": 10, "B": 20} # Used lanes: 10, 20
        
        with patch('random.choice') as mock_choice:
            # First choice: chain "A"
            # Second choice: new_y from used_lanes (10 or 20) -> Let's pick 20
            mock_choice.side_effect = ["A", 20]
            
            mutated = optimizer._mutate(individual.copy())
            
        assert mutated["A"] == 20
