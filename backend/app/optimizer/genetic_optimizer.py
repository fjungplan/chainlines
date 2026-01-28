"""
Genetic algorithm for layout optimization.
Finds optimal Y-coordinate assignments for chains using evolutionary approach.
"""
import random
import time
from typing import List, Dict, Any, Callable, Set
from app.optimizer.cost_function import calculate_single_chain_cost


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
        tournament_size: int = 3
    ):
        """
        Initialize the genetic optimizer.
        
        Args:
            pop_size: Population size
            generations: Maximum number of generations
            mutation_rate: Probability of mutation per individual
            tournament_size: Number of individuals in tournament selection
        """
        self.pop_size = pop_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        
        # Cost function weights (matching frontend config)
        self.weights = {
            "ATTRACTION": 1000.0,
            "CUT_THROUGH": 10000.0,
            "BLOCKER": 5000.0,
            "Y_SHAPE": 150.0
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
        chains = family.get("chains", [])
        links = family.get("links", [])
        
        if not chains:
            return {
                "y_indices": {},
                "score": 0.0,
                "generations_run": 0
            }
        
        # Build parent/child maps for cost calculation
        chain_parents, chain_children = self._build_relationship_maps(chains, links)
        
        # Initialize population
        population = self._initialize_population(chains)
        best_individual = None
        best_score = float('inf')
        
        generations_run = 0
        for gen in range(self.generations):
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                break
            
            generations_run += 1
            
            # Evaluate fitness for all individuals
            scored_population = []
            for individual in population:
                score = self._evaluate_fitness(
                    individual, chains, chain_parents, chain_children, links
                )
                scored_population.append((individual, score))
                
                if score < best_score:
                    best_score = score
                    best_individual = individual.copy()
            
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
                child = self._mutate(child)
                
                new_population.append(child)
            
            population = new_population
        
        return {
            "y_indices": best_individual,
            "score": best_score,
            "generations_run": generations_run
        }
    
    def _initialize_population(self, chains: List[Dict]) -> List[Dict[str, int]]:
        """
        Create initial population with diverse Y-index assignments.
        
        Args:
            chains: List of chain objects
        
        Returns:
            List of individuals (each is {chainId: yIndex})
        """
        population = []
        n_chains = len(chains)
        
        for _ in range(self.pop_size):
            # Create unique Y-indices for this individual
            y_indices = list(range(n_chains))
            random.shuffle(y_indices)
            
            individual = {
                chains[i]["id"]: y_indices[i] 
                for i in range(n_chains)
            }
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
                        # Check time overlap
                        if (start <= other_chain["endTime"] + 1 and 
                            other_chain["startTime"] <= end + 1):
                            return True
            return False
        
        # Calculate total cost
        total_cost = 0.0
        for chain in chains:
            y = individual[chain["id"]]
            cost = calculate_single_chain_cost(
                chain, y, chain_parents, chain_children, 
                links, check_collision, self.weights
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
        
        # Repair to ensure uniqueness
        self._repair_individual(child)
        return child
    
    def _mutate(self, individual: Dict[str, int]) -> Dict[str, int]:
        """
        Mutate an individual by randomly changing Y-indices.
        
        Args:
            individual: Individual to mutate
        
        Returns:
            Mutated individual
        """
        if random.random() > self.mutation_rate:
            return individual
        
        # Randomly select a chain and reassign its Y
        chain_id = random.choice(list(individual.keys()))
        n_chains = len(individual)
        
        # Pick a new Y from expanded range
        new_y = random.randint(0, n_chains + 5)
        individual[chain_id] = new_y
        
        # Repair to ensure uniqueness
        self._repair_individual(individual)
        return individual
    
    def _repair_individual(self, individual: Dict[str, int]) -> None:
        """
        Repair individual to ensure Y-indices are unique.
        
        Modifies individual in-place.
        """
        seen_ys: Set[int] = set()
        duplicates = []
        
        for chain_id, y in individual.items():
            if y in seen_ys:
                duplicates.append(chain_id)
            else:
                seen_ys.add(y)
        
        if duplicates:
            # Find available Y-indices
            max_y = max(seen_ys) if seen_ys else 0
            available = [y for y in range(max_y + len(duplicates) + 10) if y not in seen_ys]
            
            for chain_id in duplicates:
                if available:
                    new_y = random.choice(available)
                    individual[chain_id] = new_y
                    available.remove(new_y)
                    seen_ys.add(new_y)
