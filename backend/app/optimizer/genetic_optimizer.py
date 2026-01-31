"""
Genetic algorithm for layout optimization.
Finds optimal Y-coordinate assignments for chains using evolutionary approach.
"""
import random
import time
from typing import List, Dict, Any, Callable, Set
import logging
import json
import os
from app.optimizer.cost_function import calculate_single_chain_cost

logger = logging.getLogger(__name__)


class GeneticOptimizer:
    """
    Genetic algorithm optimizer for finding optimal chain Y-positions.
    
    Uses tournament selection, uniform crossover, and random mutation to
    evolve a population of Y-coordinate assignments toward lower cost layouts.
    """
    
    def __init__(
        self,
        pop_size: int = 100,
        generations: int = 500,
        mutation_rate: float = 0.10,
        tournament_size: int = 3,
        patience: int = 500,
        min_improvement: float = 0.01,
        mutation_strategies: Dict[str, float] = None
    ):
        """
        Initialize the genetic optimizer.
        
        Args:
            pop_size: Population size
            generations: Maximum number of generations
            mutation_rate: Probability of mutation per individual
            tournament_size: Number of individuals in tournament selection
            patience: Number of generations to wait for improvement before early exit
            min_improvement: Minimum improvement required to reset patience
        """
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.patience = patience
        self.min_improvement = min_improvement
        self.timeout_seconds = 3600 # Default
        
        # Cost function weights (matching frontend config)
        self.weights = {
            "ATTRACTION": 1000.0,
            "CUT_THROUGH": 10000.0,
            "BLOCKER": 5000.0,
            "Y_SHAPE": 150.0
        }
        
        # Default mutation strategies
        self.mutation_strategies = mutation_strategies or {
            "SWAP": 0.2,
            "HEURISTIC": 0.2,
            "COMPACTION": 0.3,
            "EXPLORATION": 0.3
        }
    
    def optimize(
        self,
        family: Dict[str, Any],
        timeout_seconds: int = 3600
    ) -> Dict[str, Any]:
        """
        Run genetic optimization for a family.
        
        Args:
            family: Family data with 'chains' and 'links'
            timeout_seconds: Maximum time to run (default 1 hour)
        
        Returns:
            Dict with:
                - y_indices: {chainId: yIndex}
                - score: Final cost score
                - generations_run: Number of generations completed
        """
        start_time = time.time()
        
        # Hot Reload Config (User Tweak Support)
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'layout_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    self.weights = config_data.get("WEIGHTS", self.weights)
                    # Load GA settings
                    ga_config = config_data.get("GENETIC_ALGORITHM", {})
                    self.pop_size = ga_config.get("POP_SIZE", self.pop_size)
                    self.generations = ga_config.get("GENERATIONS", self.generations)
                    self.mutation_rate = ga_config.get("MUTATION_RATE", self.mutation_rate)
                    self.tournament_size = ga_config.get("TOURNAMENT_SIZE", self.tournament_size)
                    self.timeout_seconds = ga_config.get("TIMEOUT_SECONDS", self.timeout_seconds)
                    self.patience = ga_config.get("PATIENCE", self.patience)
                    self.mutation_strategies = config_data.get("MUTATION_STRATEGIES", self.mutation_strategies)
                    logger.info(f"Loaded config from {os.path.abspath(config_path)}: pop={self.pop_size}, gens={self.generations}, mut={self.mutation_rate}, timeout={self.timeout_seconds}, patience={self.patience}")
        except Exception as e:
            logger.error(f"Failed to load layout_config.json: {e}")

        chains = family.get("chains", [])
        links = family.get("links", [])
        
        logger.info(f"Starting generic optimization for family with {len(chains)} chains, {len(links)} links")
        
        if not chains:
            return {
                "y_indices": {},
                "score": 0.0,
                "generations_run": 0,
                "best_generation": 0,
                "total_generations": 0,
                "lane_count": 0,
                "cost_breakdown": {}
            }
        
        # Build parent/child maps for cost calculation
        chain_parents, chain_children = self._build_relationship_maps(chains, links)
        
        # Initialize population at first generation
        population = self._initialize_population(chains)
        best_individual = None
        best_score = float('inf')
        best_generation = 0
        
        generations_run = 0
        generations_without_improvement = 0
        
        for gen in range(self.generations):
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                logger.warning(f"Optimization timed out after {timeout_seconds}s at generation {generations_run}")
                break
            
            # Check stagnancy
            if generations_without_improvement >= self.patience:
                logger.info(f"Score stagnated for {self.patience} generations. Early exit at {generations_run}")
                break
            
            generations_run += 1
            
            # Evaluate fitness for all individuals
            scored_population = []
            improved_this_gen = False
            
            for individual in population:
                score = self._evaluate_fitness(
                    individual, chains, chain_parents, chain_children, links
                )
                scored_population.append((individual, score))
                
                if score < best_score - self.min_improvement:
                    best_score = score
                    best_individual = individual.copy()
                    improved_this_gen = True
                    best_generation = generations_run
            
            if improved_this_gen:
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            
            # Create score lookup for selection
            score_map = {id(ind): score for ind, score in scored_population}
            
            # Generate next generation
            new_population = [best_individual.copy()]  # Elitism
            
            while len(new_population) < self.pop_size:
                # Selection
                parent1 = self._tournament_select(
                    population, 
                    lambda ind: score_map[id(ind)],
                    self.tournament_size
                )
                parent2 = self._tournament_select(
                    population,
                    lambda ind: score_map[id(ind)],
                    self.tournament_size
                )
                
                # Crossover
                child = self._crossover(parent1, parent2)
                
                # Mutation
                child = self._mutate(child, chain_parents, chain_children)
                
                new_population.append(child)
            
            population = new_population
            if generations_run % 10 == 0:
                logger.info(f"Generation {generations_run}/{self.generations} completed. Best score so far: {best_score:.2f}")

        # Calculate final cost breakdown for best solution
        vertical_segments = self._generate_vertical_segments(chains, chain_parents, best_individual)
        y_slots = {}
        for chain_id, y in best_individual.items():
            if y not in y_slots: y_slots[y] = []
            c_orig = next(c for c in chains if c["id"] == chain_id)
            y_slots[y].append({"start": c_orig["startTime"], "end": c_orig["endTime"], "chainId": chain_id})

        def final_check_collision(lane, start, end, exclude_id, chain_obj):
            slots = y_slots.get(lane, [])
            for s in slots:
                if s["chainId"] == exclude_id: continue
                if not (end < s["start"] or start > s["end"]): return True
            return False

        final_breakdown = {
            "ATTRACTION": {"multiplier": 0.0, "sum": 0.0},
            "CUT_THROUGH": {"multiplier": 0, "sum": 0.0},
            "BLOCKER": {"multiplier": 0, "sum": 0.0},
            "Y_SHAPE": {"multiplier": 0, "sum": 0.0},
            "OVERLAP": {"multiplier": 0.0, "sum": 0.0},
            "SPACING": {"multiplier": 0, "sum": 0.0}
        }
        
        # Apply best_individual y-indices to chain objects for accurate cost calculation
        # (Otherwise parents are at original yIndex usually 0, causing huge attraction costs)
        chain_map = {c["id"]: c for c in chains}
        for chain_id, y in best_individual.items():
            if chain_id in chain_map:
                chain_map[chain_id]["yIndex"] = y

        for chain in chains:
            res = calculate_single_chain_cost(
                chain, best_individual[chain["id"]], chain_parents, chain_children,
                vertical_segments, final_check_collision, self.weights, y_slots,
                return_breakdown=True
            )
            for key, val in res["breakdown"].items():
                final_breakdown[key]["multiplier"] += val["multiplier"]
                final_breakdown[key]["sum"] += val["sum"]

        return {
            "y_indices": best_individual,
            "score": best_score,
            "generations_run": generations_run,
            "best_generation": best_generation,
            "total_generations": generations_run,
            "lane_count": len(set(best_individual.values())),
            "cost_breakdown": final_breakdown
        }
    
    def _initialize_population(self, chains: List[Dict]) -> List[Dict[str, int]]:
        """
        Create initial population with diverse Y-index assignments.
        
        Optimized for compactness:
        - Allows multiple chains in same lane (if times don't overlap)
        - Initializes in a compressed range to reduce attraction costs
        """
        population = []
        n_chains = len(chains)
        
        # Heuristic: Try to fit in roughly sqrt(N) to N/2 lanes
        initial_lanes = max(3, int(n_chains ** 0.6))
        
        for _ in range(self.pop_size):
            individual = {}
            for i in range(n_chains):
                # Randomly assign to a compact set of lanes
                # yielding a dense initial map
                individual[chains[i]["id"]] = random.randint(0, initial_lanes)
            
            population.append(individual)
        
        return population
    
    def _build_relationship_maps(
        self, 
        chains: List[Dict], 
        links: List[Dict]
    ) -> tuple[Dict[str, List[Dict]], Dict[str, List[Dict]]]:
        """Build parent and child relationship maps."""
        chain_parents = {}
        chain_children = {}
        chain_map = {c["id"]: c for c in chains}
        
        for link in links:
            parent_id = link["parentId"]
            child_id = link["childId"]
            
            if child_id not in chain_parents:
                chain_parents[child_id] = []
            if parent_id not in chain_children:
                chain_children[parent_id] = []
            
            if parent_id in chain_map:
                chain_parents[child_id].append(chain_map[parent_id])
            if child_id in chain_map:
                chain_children[parent_id].append(chain_map[child_id])
        
        return chain_parents, chain_children
    
    def _generate_vertical_segments(
        self,
        chains: List[Dict],
        chain_parents: Dict[str, List[Dict]],
        individual: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """
        Generate vertical segments for blocker penalty calculation.
        
        A vertical segment is created when a parent and child are more than
        1 lane apart (non-adjacent), representing the vertical connection line.
        
        Args:
            chains: List of chain objects
            chain_parents: Map of child chain ID to parent chain objects
            individual: Current Y-index assignment {chainId: yIndex}
        
        Returns:
            List of segment dicts with {y1, y2, time, childId, parentId}
        """
        vertical_segments = []
        
        for chain in chains:
            chain_id = chain["id"]
            chain_y = individual.get(chain_id, 0)
            parents = chain_parents.get(chain_id, [])
            
            for parent in parents:
                parent_y = individual.get(parent["id"], 0)
                
                # Only create segment if they are NOT adjacent (more than 1 lane apart)
                if abs(parent_y - chain_y) > 1:
                    vertical_segments.append({
                        "y1": min(parent_y, chain_y),
                        "y2": max(parent_y, chain_y),
                        "time": chain["startTime"],
                        "childId": chain_id,
                        "parentId": parent["id"]
                    })
        
        return vertical_segments
    
    def _evaluate_fitness(
        self,
        individual: Dict[str, int],
        chains: List[Dict],
        chain_parents: Dict[str, List[Dict]],
        chain_children: Dict[str, List[Dict]],
        links: List[Dict]
    ) -> float:
        """
        Calculate fitness (cost) of an individual.
        
        Lower cost = better fitness.
        """
        # Temporarily assign yIndex to chains
        chain_map = {c["id"]: c for c in chains}
        original_y_indices = {}
        
        for chain_id, y_index in individual.items():
            if chain_id in chain_map:
                original_y_indices[chain_id] = chain_map[chain_id].get("yIndex")
                chain_map[chain_id]["yIndex"] = y_index
        
        # Create collision checker
        def check_collision(lane, start, end, exclude_id, chain_obj):
            for other_id, other_y in individual.items():
                if other_id == exclude_id:
                    continue
                if other_y == lane:
                    other_chain = chain_map.get(other_id)
                    if other_chain:
                        # Check relationship
                        is_family = False
                        # Check parents
                        if other_id in [p["id"] for p in chain_parents.get(exclude_id, [])]:
                            is_family = True
                        # Check children
                        elif other_id in [c["id"] for c in chain_children.get(exclude_id, [])]:
                            is_family = True
                            
                        # Collision logic
                        if is_family:
                            # Family: Allow touching (no gap required)
                            # Overlap only if actual years overlap
                            if (start <= other_chain["endTime"] and 
                                other_chain["startTime"] <= end):
                                return True
                        else:
                            # Strangers: Require 1 year gap
                            # Collision if gap < 1
                            if (start <= other_chain["endTime"] + 1 and 
                                other_chain["startTime"] <= end + 1):
                                return True
            return False
        
        # Generate vertical segments for blocker penalty
        vertical_segments = self._generate_vertical_segments(
            chains, chain_parents, individual
        )

        # Build y_slots for Lane Sharing calculation
        y_slots = {}
        for chain_id, y in individual.items():
            if chain_id in chain_map:
                if y not in y_slots:
                    y_slots[y] = []
                c = chain_map[chain_id]
                y_slots[y].append({
                    "start": c["startTime"],
                    "end": c["endTime"],
                    "chainId": chain_id
                })
        
        # Calculate total cost
        total_cost = 0.0
        for chain in chains:
            y = individual[chain["id"]]
            cost = calculate_single_chain_cost(
                chain, y, chain_parents, chain_children, 
                vertical_segments, check_collision, self.weights,
                y_slots=y_slots
            )
            total_cost += cost
        
        # Restore original y_indices
        for chain_id, orig_y in original_y_indices.items():
            if orig_y is not None:
                chain_map[chain_id]["yIndex"] = orig_y
        
        return total_cost
    
    def _tournament_select(
        self,
        population: List[Dict[str, int]],
        get_score: Callable[[Dict], float],
        tournament_size: int
    ) -> Dict[str, int]:
        """
        Select individual using tournament selection.
        
        Args:
            population: List of individuals
            get_score: Function to get score for an individual
            tournament_size: Number of individuals in tournament
        
        Returns:
            Selected individual
        """
        tournament = random.sample(population, min(tournament_size, len(population)))
        return min(tournament, key=get_score)
    
    def _crossover(
        self,
        parent1: Dict[str, int],
        parent2: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Perform uniform crossover between two parents.
        
        Args:
            parent1: First parent
            parent2: Second parent
        
        Returns:
            Child individual
        """
        child = {}
        for chain_id in parent1.keys():
        # Uniform crossover: randomly pick from each parent
            child[chain_id] = parent1[chain_id] if random.random() < 0.5 else parent2[chain_id]
        
        # No repair needed - valid to have duplicates
        return child
    
    def _mutate(
        self, 
        individual: Dict[str, int],
        chain_parents: Dict[str, List[Dict]] = None,
        chain_children: Dict[str, List[Dict]] = None
    ) -> Dict[str, int]:
        """
        Mutate an individual using multiple strategies.
        
        Strategies:
        - 30% Compaction: Move to random used lane
        - 30% Exploration: Move to random variable/empty lane
        - 20% Swap: Switch positions of two chains (Topology fix)
        - 20% Heuristic: Move to Parent/Child lane (Smart move)
        """
        if random.random() > self.mutation_rate:
            return individual
        
        rand_val = random.random()
        
        # Strategy Selection via Config
        s = self.mutation_strategies
        swap_thresh = s.get("SWAP", 0.0)
        heuristic_thresh = swap_thresh + s.get("HEURISTIC", 0.0)
        compaction_thresh = heuristic_thresh + s.get("COMPACTION", 0.0)
        
        if rand_val < swap_thresh:
            # Swap Strategy
            return self._mutate_swap(individual)
        elif rand_val < heuristic_thresh and chain_parents is not None:
             # Heuristic Strategy (if context available)
             return self._mutate_heuristic(individual, chain_parents, chain_children)
        elif rand_val < compaction_thresh:
             # Compaction Strategy
             strategy = "compaction"
        else:
             # Exploration Strategy
             strategy = "exploration"
             
        # Standard Move Logic (Compaction/Exploration)
        chain_id = random.choice(list(individual.keys()))
        used_lanes = list(set(individual.values()))
        max_y = max(used_lanes) if used_lanes else 0
        
        if strategy == "compaction" and used_lanes:
            new_y = random.choice(used_lanes)
        else:
            new_y = random.randint(0, max_y + 2)
            
        individual[chain_id] = new_y
        return individual

    def _mutate_swap(self, individual: Dict[str, int]) -> Dict[str, int]:
        """Swap Y-indices of two random chains."""
        if len(individual) < 2:
            return individual
            
        keys = list(individual.keys())
        a, b = random.sample(keys, 2)
        individual[a], individual[b] = individual[b], individual[a]
        return individual

    def _mutate_heuristic(
        self,
        individual: Dict[str, int],
        chain_parents: Dict[str, List[Dict]],
        chain_children: Dict[str, List[Dict]]
    ) -> Dict[str, int]:
        """
        Smart move: Attempt to move a chain to the same lane as its parent or child.
        """
        chain_id = random.choice(list(individual.keys()))
        target_y = None
        
        # 1. Try moving to Parent's Y
        parents = chain_parents.get(chain_id, [])
        if parents:
            # Pick valid parent (one that exists in individual)
            valid_p = [p for p in parents if p["id"] in individual]
            if valid_p:
                target_p = random.choice(valid_p)
                target_y = individual[target_p["id"]]
        
        # 2. If no parent target, try Child's Y
        if target_y is None:
            children = chain_children.get(chain_id, [])
            if children:
                valid_c = [c for c in children if c["id"] in individual]
                if valid_c:
                    target_c = random.choice(valid_c)
                    target_y = individual[target_c["id"]]
        
        # Apply move if target found
        if target_y is not None:
            individual[chain_id] = target_y
            
        return individual
    
    
    def _repair_individual(self, individual: Dict[str, int]) -> None:
        """Deprecated/No-op. Uniqueness is not required."""
        pass
