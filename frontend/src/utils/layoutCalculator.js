import { VISUALIZATION } from '../constants/visualization';

/**
 * Configuration for the Physics Layout Engine
 * Tuned for global convergence of large blocks and tight local clustering.
 */
export const LAYOUT_CONFIG = {
  // Iteration Control
  ITERATIONS: {
    MIN: 50,              // Minimum for tiny families
    MAX: 500,             // Cap for huge families
    MULTIPLIER: 10        // Iterations per chain (N * 10)
  },

  // Search Space
  SEARCH_RADIUS: 50,        // Look +/- 50 lanes away for a better spot (Global Vision)
  TARGET_RADIUS: 10,        // Look +/- 10 lanes around the exact parent/child center (Precision Snapping)

  // Forces & Penalties (Cost Function)
  WEIGHTS: {
    ATTRACTION: 100.0,       // Pull per lane of distance (High = tight families)
    CUT_THROUGH: 10000.0,   // Penalty for being sliced by a vertical link (Avoids crossings)
    BLOCKER: 5000.0,        // Penalty for sitting on someone else's link (Get out of the way)
    LANE_SHARING: 500.0,    // Base Penalty for sharing (Decays with distance: 500/Gap)
    Y_SHAPE: 150.0,         // Penalty for "Uneven" Merges/Splits (Forces Spouses/Siblings 2 lanes apart)
  }
};

/**
 * Calculate positions for all nodes using Sankey-like layout
 */
export class LayoutCalculator {
  constructor(graphData, width, height, yearRange = null, stretchFactor = 1) {
    this.nodes = graphData.nodes;
    this.links = graphData.links;
    this.width = width;
    this.height = height;
    this.stretchFactor = stretchFactor;

    console.log('LayoutCalculator constructor:');
    console.log('  Total nodes:', this.nodes.length);
    console.log('  First 3 nodes:', this.nodes.slice(0, 3).map(n => ({
      id: n.id,
      name: n.eras?.[0]?.name,
      founding: n.founding_year,
      dissolution: n.dissolution_year,
      era_years: n.eras.map(e => e.year)
    })));
    console.log('  First node keys:', Object.keys(this.nodes[0] || {}));

    // Always calculate yearRange from actual node data to ensure xScale covers all nodes
    // The yearRange parameter (filterYearRange) is ignored; we use the real data
    this.yearRange = this.calculateYearRange();
    this.xScale = this.createXScale();

    // Calculate pixelsPerYear for proportional vertical scaling
    const padding = 50;
    const availableWidth = this.width - 2 * padding;
    const span = this.yearRange.max - this.yearRange.min;
    this.pixelsPerYear = (availableWidth / span) * this.stretchFactor;

    // Dynamic Vertical Scaling
    // Node Height = pixelsPerYear * HEIGHT_FACTOR
    this.nodeHeight = this.pixelsPerYear * VISUALIZATION.HEIGHT_FACTOR;

    // Row Height = Node Height * 1.5
    // Effectively caps row height at 60px
    this.rowHeight = this.nodeHeight * 1.5;

    console.log('LayoutCalculator Vertical Scaling:', {
      pixelsPerYear: this.pixelsPerYear,
      nodeHeight: this.nodeHeight,
      rowHeight: this.rowHeight,
      factor: VISUALIZATION.HEIGHT_FACTOR
    });
  }

  calculateYearRange() {
    const allYears = [];
    const eraYears = [];
    const foundingYears = [];
    const dissolutionYears = [];

    // Get years from eras
    this.nodes.forEach(node => {
      node.eras.forEach(era => {
        eraYears.push(era.year);
        allYears.push(era.year);
      });
      // Also include founding and dissolution years
      foundingYears.push(node.founding_year);
      allYears.push(node.founding_year);
      if (node.dissolution_year) {
        dissolutionYears.push(node.dissolution_year);
        allYears.push(node.dissolution_year);
      }
    });

    // Include current year so active teams extend to today
    const currentYear = new Date().getFullYear();
    allYears.push(currentYear);

    // Calculate range from actual data without arbitrary minimums
    const minYear = Math.min(...allYears, 1900);
    const maxYear = Math.max(...allYears);

    // Debug logging
    console.log('calculateYearRange: eraYears min/max:', Math.min(...eraYears), '/', Math.max(...eraYears));
    console.log('calculateYearRange: foundingYears min/max:', Math.min(...foundingYears), '/', Math.max(...foundingYears));
    console.log('calculateYearRange: dissolutionYears min/max:', Math.min(...dissolutionYears), '/', Math.max(...dissolutionYears));
    console.log('calculateYearRange: currentYear:', currentYear);
    console.log('calculateYearRange: final min/max:', minYear, '/', maxYear, 'returned range:', minYear, '-', maxYear + 1);

    // Add +1 year to show the full span of the final year
    return {
      min: minYear,
      max: maxYear + 1
    };
  }

  createXScale() {
    // Map years to X coordinates
    const padding = 50;
    const { min, max } = this.yearRange;
    const span = max - min;
    const availableWidth = this.width - 2 * padding;
    const pixelsPerYear = (availableWidth / span) * this.stretchFactor;

    console.log(`createXScale: this.width=${this.width}, padding=${padding}, availableWidth=${availableWidth}, stretchFactor=${this.stretchFactor}`);
    console.log(`  yearRange=${min}-${max}, span=${span}`);
    console.log(`  pixelsPerYear=${pixelsPerYear.toFixed(4)}`);
    console.log(`  Example: year 2000 should map to ${padding + ((2000 - min) / span) * availableWidth}, year 2008 should map to ${padding + ((2008 - min) / span) * availableWidth}`);

    return (year) => {
      const range = max - min;
      const position = (year - min) / range;
      const result = padding + (position * (this.width - 2 * padding) * this.stretchFactor);
      // Only log for key years to avoid spam
      if ([1900, 2000, 2007, 2008, 2025, 2026, this.yearRange.max - 1].includes(year)) {
        console.log(`  xScale(${year}) = ${result.toFixed(2)} [position=${position.toFixed(4)}, effective_width=${this.width - 2 * padding}]`);
      }
      return result;
    };
  }

  calculateLayout() {
    // Step 1: Assign X positions based on founding year
    const nodesWithX = this.assignXPositions();

    // Step 2: Assign Y positions to minimize crossings
    const { positioned, rowHeight } = this.assignYPositions(nodesWithX);

    // Step 3: Calculate link paths
    const linkPaths = this.calculateLinkPaths(positioned);

    return {
      nodes: positioned,
      links: linkPaths,
      yearRange: this.yearRange,
      xScale: this.xScale,
      rowHeight,
      nodeHeight: this.nodeHeight,
      pixelsPerYear: this.pixelsPerYear
    };
  }

  assignXPositions() {
    return this.nodes.map(node => {
      console.log(`assignXPositions - ${node.eras?.[0]?.name}: dissolution_year=${node.dissolution_year}`);
      return {
        ...node,
        x: this.xScale(node.founding_year),
        width: this.calculateNodeWidth(node)
      };
    });
  }

  calculateNodeWidth(node) {
    // Node should span from start of founding year to END of dissolution year
    // A team founded in 2000 and dissolved in 2005 should span 2000-2005 inclusive
    // So width = xScale(2006) - xScale(2000) to reach the grid line at start of 2006
    // Active teams (no dissolution) extend to current year boundary without +1
    const startX = this.xScale(node.founding_year);
    let endX;
    const teamName = node.eras?.[0]?.name || `Node ${node.id}`;

    if (node.dissolution_year) {
      // Dissolved: extend to start of next year after dissolution
      endX = this.xScale(node.dissolution_year + 1);
      const scaledWidth = endX - startX;
      console.log(`${teamName}: [${node.founding_year}-${node.dissolution_year}] startX=${startX.toFixed(2)}, endX(${node.dissolution_year + 1})=${endX.toFixed(2)}, width=${scaledWidth.toFixed(2)}`);
      // DON'T apply MIN_NODE_WIDTH for dissolved teams - keep accurate year boundaries
      return scaledWidth;
    } else {
      // Logic for teams with NO dissolution year
      // Check if they are actually active (last era is recent)
      const lastEra = node.eras && node.eras.length > 0
        ? node.eras.reduce((max, era) => (!max || era.year > max.year ? era : max), null)
        : null;

      const currentYear = new Date().getFullYear();
      // Consider active if last era is this year or last year (allowing for data lag)
      const isActive = lastEra && lastEra.year >= (currentYear - 1);

      if (isActive) {
        // Active: extend to end of yearRange
        endX = this.xScale(this.yearRange.max);
        const scaledWidth = endX - startX;
        // For active teams, apply MIN_NODE_WIDTH
        return Math.max(VISUALIZATION.MIN_NODE_WIDTH, scaledWidth);
      } else {
        // Inactive (Zombie team): Cap at last known era
        // This fixes "infinite bar" for teams that just stopped existing without a dissolution year
        const endYear = lastEra ? lastEra.year + 1 : node.founding_year + 1;
        endX = this.xScale(endYear);
        const scaledWidth = endX - startX;
        return scaledWidth; // Accurate duration, no min width padding
      }
    }
  }

  assignYPositions(nodes) {
    // Phase 1: Chain Decomposition
    const chains = this.buildChains(nodes, this.links);

    // Phase 2: Macro-Level Organization (Family Stacking)
    const families = this.buildFamilies(chains);

    // Phase 3: Micro-Level Layout (Per Family)
    const activeLanes = new Map(); // Global tracking to prevent overlaps if we were doing global, 
    // but we are doing stacked families.

    let globalYOffset = 50;
    const positionedNodes = [];

    families.forEach(family => {
      // Layout this family internally
      const familyHeight = this.layoutFamily(family);

      // Assign final Y coordinates based on global stack
      family.chains.forEach(chain => {
        const chainY = globalYOffset + (chain.yIndex * this.rowHeight);
        chain.nodes.forEach(node => {
          node.y = chainY;
          node.height = this.nodeHeight;
          positionedNodes.push(node);
        });
      });

      // No padding between families as requested by user
      globalYOffset += familyHeight;
    });

    return { positioned: positionedNodes, rowHeight: this.rowHeight };
  }

  buildChains(nodes, links) {
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const preds = new Map();
    const succs = new Map();

    // specific check for 1-to-1ness
    links.forEach(l => {
      if (!preds.has(l.target)) preds.set(l.target, []);
      if (!succs.has(l.source)) succs.set(l.source, []);
      preds.get(l.target).push(l.source);
      succs.get(l.source).push(l.target);
    });

    const chains = [];
    const visited = new Set();

    // 1. Identification of "Chain Starter" nodes
    // A node starts a chain if:
    // - It has 0 predecessors 
    // - OR It has > 1 predecessors (Merge)
    // - OR Its predecessor has > 1 successors (Split parent)

    const isChainStart = (nodeId) => {
      const p = preds.get(nodeId) || [];
      if (p.length !== 1) return true; // 0 or >1 preds
      const parentId = p[0];
      const parentSuccs = succs.get(parentId) || [];
      if (parentSuccs.length > 1) return true; // Parent splits

      // ALSO: Check for temporal overlap with the single parent.
      // If we overlap, we MUST be a chain start (because parent broke the chain).
      const parentNode = nodeMap.get(parentId);
      const myNode = nodeMap.get(nodeId);

      let parentEnd = parentNode.dissolution_year;
      if (!parentEnd) {
        const lastEra = parentNode.eras?.[parentNode.eras.length - 1];
        parentEnd = lastEra ? lastEra.year : parentNode.founding_year;
      }

      if (parentEnd > myNode.founding_year) return true; // Parent overlaps me, so I start new

      return false; // Linear, no overlap
    };

    nodes.forEach(node => {
      if (visited.has(node.id)) return;

      // If it's a start node, build a chain from it
      // Note: If we traverse properly, we only need to find start nodes.
      // However, cycles might confuse this. For DAGs (timelines), this works.
      // To be safe, we iterate all, and if unvisited and isChainStart, we consume.
      if (isChainStart(node.id)) {
        const chainNodes = [];
        let curr = node.id;

        while (curr) {
          visited.add(curr);
          chainNodes.push(nodeMap.get(curr));

          const s = succs.get(curr) || [];
          // Stop if:
          // - No successors
          // - > 1 successors (Split) -> curr is LAST in this chain
          // - Successor has > 1 predecessors (Merge) -> succ is START of NEW chain
          if (s.length !== 1) break;

          const nextId = s[0];
          const nextPreds = preds.get(nextId) || [];
          if (nextPreds.length > 1) break;

          // Continue
          // CRITICAL: Check for temporal overlap (Dirty Data Protection)
          // If curr ends AFTER next starts, they visually overlap on the same row.
          // We MUST break the chain here to force them onto different rows (parent/child relationship).
          const currNode = nodeMap.get(curr);
          const nextNode = nodeMap.get(nextId);

          // Use a tolerance of 0. If curr.dissolution_year (or inferred end) > next.founding_year
          // But strict inequality might be too aggressive if they effectively touch.
          // Let's assume touch is fine (end == start). Overlap is end > start.

          let currEnd = currNode.dissolution_year;
          if (!currEnd) {
            const lastEra = currNode.eras?.[currNode.eras.length - 1];
            currEnd = lastEra ? lastEra.year : currNode.founding_year;
          }

          if (currEnd > nextNode.founding_year) {
            // Overlap detected!
            break;
          }

          curr = nextId;
        }

        chains.push({
          id: `chain-${chains.length}`,
          nodes: chainNodes,
          startTime: chainNodes[0].founding_year,
          endTime: chainNodes[chainNodes.length - 1].dissolution_year || 9999,
          yIndex: 0 // to be assigned
        });
      }
    });

    // Catch-up: If any nodes remain unvisited (e.g. part of a cycle or logic gap), make them single chains
    nodes.forEach(node => {
      if (!visited.has(node.id)) {
        visited.add(node.id);
        chains.push({
          id: `chain-${chains.length}`,
          nodes: [node],
          startTime: node.founding_year,
          endTime: node.dissolution_year || 9999,
          yIndex: 0
        });
      }
    });

    return chains;
  }

  buildFamilies(chains) {
    // Group chains into connected components
    const chainMap = new Map(); // nodeId -> chainId
    chains.forEach(c => c.nodes.forEach(n => chainMap.set(n.id, c)));

    const adj = new Map();
    chains.forEach(c => adj.set(c, new Set()));

    this.links.forEach(l => {
      const c1 = chainMap.get(l.source);
      const c2 = chainMap.get(l.target);
      if (c1 && c2 && c1 !== c2) {
        adj.get(c1).add(c2);
        adj.get(c2).add(c1);
      }
    });

    const families = [];
    const visited = new Set();

    chains.forEach(c => {
      if (visited.has(c)) return;
      const familyChains = [];
      const q = [c];
      visited.add(c);

      let minStart = c.startTime;

      while (q.length) {
        const cur = q.shift();
        familyChains.push(cur);
        if (cur.startTime < minStart) minStart = cur.startTime;

        adj.get(cur).forEach(neighbor => {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            q.push(neighbor);
          }
        });
      }

      families.push({
        chains: familyChains,
        minStart
      });
    });

    // Sort families by start year (Gantt style), then by size (largest first)
    families.sort((a, b) => {
      if (a.minStart !== b.minStart) return a.minStart - b.minStart;
      // Tie-breaker: larger families first (optional preference)
      if (a.chains.length !== b.chains.length) return b.chains.length - a.chains.length;
      // Tie-breaker: ID stability (assuming chains[0] exists)
      return a.chains[0].id.localeCompare(b.chains[0].id);
    });

    return families;
  }

  layoutFamily(family) {
    if (family.chains.length === 0) return 0;

    // 1. Initial Placement (Topological / Barycenter guess)
    // Sort chains by start time to process legal parents first
    family.chains.sort((a, b) => a.startTime - b.startTime);

    const ySlots = new Map(); // yIndex -> Array of {start, end, chainId}
    let maxY = 0;

    const checkCollision = (y, start, end, excludeChainId) => {
      if (!ySlots.has(y)) return false;
      const slots = ySlots.get(y);
      // Check intersection: !(end1 < start2 || start1 > end2)
      // Strict inequality ensures that if End1 == Start2 (shared year), it IS a collision.
      // because End1 < Start2 is FALSE.
      const collision = slots.some(s => {
        if (s.chainId === excludeChainId) return false;
        // Debug
        const collide = !(s.end < start || s.start > end);
        if (collide && (s.end === start || s.start === end)) {
          // console.log(`Strict Collision Conflict: Lane ${y}. Existing [${s.start}-${s.end}] vs New [${start}-${end}]`);
        }
        return collide;
      });
      return collision;
    };

    const occupySlot = (y, chain) => {
      if (!ySlots.has(y)) ySlots.set(y, []);
      ySlots.get(y).push({ start: chain.startTime, end: chain.endTime, chainId: chain.id });
      chain.yIndex = y;
      if (y > maxY) maxY = y;
    };

    // Calculate parents map for forces
    // chainId -> [parentChainId, ...]
    const chainParents = new Map();
    const nodeToChain = new Map();
    family.chains.forEach(c => c.nodes.forEach(n => nodeToChain.set(n.id, c)));

    family.chains.forEach(c => {
      const parents = new Set();
      const firstNode = c.nodes[0];
      // Find links pointing to firstNode
      this.links.forEach(l => {
        if (l.target === firstNode.id) {
          const pChain = nodeToChain.get(l.source);
          if (pChain && pChain !== c) parents.add(pChain);
        }
      });
      chainParents.set(c.id, Array.from(parents));
    });

    // Initial Placement
    // STRATEGY CHANGE: Instead of sorting by StartTime (Temporal packing),
    // we use a BFS/Hierarchy traversal to place Children immediately after Parents.
    // This prioritizes Lineage Locality (child near parent) over global packing.

    const placedChains = new Set();
    const chainsToPlace = [...family.chains].sort((a, b) => a.startTime - b.startTime); // Default pool

    // Helper to pick next chain
    // 1. Pick a chain whose parents are already placed.
    // 2. If none, pick the earliest unplaced chain (new root).

    // We already built 'chainParents'. Let's build 'chainChildren' for traversal.
    const chainChildrenMap = new Map();
    family.chains.forEach(c => chainChildrenMap.set(c.id, []));

    // Populate children map
    family.chains.forEach(child => {
      const parents = chainParents.get(child.id) || [];
      parents.forEach(p => {
        chainChildrenMap.get(p.id).push(child);
      });
    });

    const queue = [];
    // Initialize queue with roots (no parents)
    const roots = family.chains.filter(c => (chainParents.get(c.id) || []).length === 0);
    // Sort roots by start time to keep top-left sanity
    roots.sort((a, b) => a.startTime - b.startTime);
    roots.forEach(r => queue.push(r));

    // Consumed set to avoid re-queueing
    const queuedIds = new Set(roots.map(r => r.id));

    // Fallback list for disconnected or cycle-remainder nodes
    let fallbackIndex = 0;

    const processChain = (chain) => {
      let targetY = 0;
      const parents = chainParents.get(chain.id) || [];
      const placedParents = parents.filter(p => placedChains.has(p.id));

      if (placedParents.length > 0) {
        // Barycenter of parents
        // FIX: Removed double division. sumY is sum.
        const sumY = placedParents.reduce((sum, p) => sum + p.yIndex, 0);
        targetY = Math.round(sumY / placedParents.length);
      } else {
        // scan for lowest free Y from 0?
        // Or just 0. Spiral search works outwards.
        targetY = 0;
      }

      // Spiral Search
      let placed = false;
      let offset = 0;
      while (!placed) {
        let candidate = targetY + offset;
        if (candidate >= 0 && !checkCollision(candidate, chain.startTime, chain.endTime, chain.id)) {
          occupySlot(candidate, chain);
          placed = true;
          break;
        }
        if (offset > 0) {
          candidate = targetY - offset;
          if (candidate >= 0 && !checkCollision(candidate, chain.startTime, chain.endTime, chain.id)) {
            occupySlot(candidate, chain);
            placed = true;
            break;
          }
        }
        offset++;
        if (offset > 100) {
          occupySlot(maxY + 1, chain);
          placed = true;
        }
      }
      placedChains.add(chain.id);

      // Add children to queue
      const children = chainChildrenMap.get(chain.id) || [];
      // Sort children by start time
      children.sort((a, b) => a.startTime - b.startTime);

      children.forEach(child => {
        if (!queuedIds.has(child.id)) {
          queuedIds.add(child.id);
          queue.push(child);
        }
      });
    };

    while (placedChains.size < family.chains.length) {
      if (queue.length > 0) {
        const chain = queue.shift();
        processChain(chain);
      } else {
        // Pick from fallback (earliest unplaced)
        while (fallbackIndex < chainsToPlace.length && placedChains.has(chainsToPlace[fallbackIndex].id)) {
          fallbackIndex++;
        }
        if (fallbackIndex < chainsToPlace.length) {
          const chain = chainsToPlace[fallbackIndex];
          if (!queuedIds.has(chain.id)) {
            queuedIds.add(chain.id);
            queue.push(chain);
          }
        }
      }
    }

    // 2. Iterative Relaxation (Force-Directed with Cost Function)
    const ITERATIONS = Math.min(
      LAYOUT_CONFIG.ITERATIONS.MAX,
      Math.max(
        LAYOUT_CONFIG.ITERATIONS.MIN,
        family.chains.length * LAYOUT_CONFIG.ITERATIONS.MULTIPLIER
      )
    );

    // Map children for outgoing link checks
    const chainChildren = new Map();
    family.chains.forEach(c => chainChildren.set(c.id, []));

    // Iterate all chains to populate their parents' children list
    // AND Calculate Degree (Connectivity) for Gravity Sort
    const chainDegrees = new Map();

    family.chains.forEach(childChain => {
      // Init degree if not present
      if (!chainDegrees.has(childChain.id)) chainDegrees.set(childChain.id, 0);

      const parents = chainParents.get(childChain.id) || [];
      // Add In-Degree (1 per parent)
      chainDegrees.set(childChain.id, chainDegrees.get(childChain.id) + parents.length);

      parents.forEach(p => {
        // Init parent degree
        if (!chainDegrees.has(p.id)) chainDegrees.set(p.id, 0);
        // Add Out-Degree to Parent
        chainDegrees.set(p.id, chainDegrees.get(p.id) + 1);

        if (chainChildren.has(p.id)) {
          chainChildren.get(p.id).push(childChain);
        }
      });
    });

    // Pre-calculate all active vertical segments to optimize "Blocker Penalty"
    // List of { y1, y2, time, childId, parentId }
    let verticalSegments = [];
    const rebuildSegments = () => {
      verticalSegments = [];
      family.chains.forEach(chain => {
        // Incoming (Parents)
        const parents = chainParents.get(chain.id) || [];
        parents.forEach(p => {
          if (Math.abs(p.yIndex - chain.yIndex) > 1) {
            verticalSegments.push({
              y1: Math.min(p.yIndex, chain.yIndex),
              y2: Math.max(p.yIndex, chain.yIndex),
              time: chain.startTime,
              childId: chain.id,
              parentId: p.id
            });
          }
        });
        // Outgoing not needed (covered by child's incoming)
      });
    };

    const calculateCost = (chain, y) => {
      // 1. Attraction (Distance to connected nodes)
      // STRATEGY: Quadratic Bi-Directional Attraction.
      // Dist^2 punishment forces long links to snap, overcoming local penalties.

      let attractionCost = 0;
      const ATTRACTION_WEIGHT = LAYOUT_CONFIG.WEIGHTS.ATTRACTION;

      const parents = chainParents.get(chain.id) || [];
      if (parents.length > 0) {
        const avgParentY = parents.reduce((sum, p) => sum + p.yIndex, 0) / parents.length;
        const dist = Math.abs(y - avgParentY);
        attractionCost += (dist * dist) * ATTRACTION_WEIGHT;
      }

      const childrenForAttraction = chainChildren.get(chain.id) || [];
      if (childrenForAttraction.length > 0) {
        const avgChildY = childrenForAttraction.reduce((sum, c) => sum + c.yIndex, 0) / childrenForAttraction.length;
        const dist = Math.abs(y - avgChildY);
        attractionCost += (dist * dist) * ATTRACTION_WEIGHT;
      }

      // 2. Cut-Through Penalty (Self Crossing)
      let cutThroughCost = 0;
      const PENALTY = LAYOUT_CONFIG.WEIGHTS.CUT_THROUGH;

      // Check Incoming Links (Parent -> Chain)
      parents.forEach(p => {
        const y1 = Math.min(p.yIndex, y);
        const y2 = Math.max(p.yIndex, y);
        if (y2 - y1 > 1) {
          // Check if intermediate lanes are blocked
          for (let lane = y1 + 1; lane < y2; lane++) {
            if (checkCollision(lane, chain.startTime, chain.startTime, chain.id)) {
              cutThroughCost += PENALTY;
            }
          }
        }
      });

      // Check Outgoing Links (Chain -> Child)
      // Note: Children are FIXED at their current yIndex during this calc
      // So we interpret "If I move to Y, how does it affect links to my children?"
      const children = chainChildren.get(chain.id) || [];
      children.forEach(c => {
        const y1 = Math.min(y, c.yIndex);
        const y2 = Math.max(y, c.yIndex);
        if (y2 - y1 > 1) {
          for (let lane = y1 + 1; lane < y2; lane++) {
            if (checkCollision(lane, c.startTime, c.startTime, chain.id)) {
              cutThroughCost += PENALTY;
            }
          }
        }
      });

      // 3. Blocker Penalty (Am I blocking others?)
      // If 'chain' is at 'y', does it intersect any vertical segment?
      // Segment: y1 < y < y2 AND time within chain [start, end]
      let blockerCost = 0;
      const BLOCKER_PENALTY = LAYOUT_CONFIG.WEIGHTS.BLOCKER;

      verticalSegments.forEach(seg => {
        // IGNORANCE IS BLISS: Don't count my own links as obstacles!
        if (seg.childId === chain.id || seg.parentId === chain.id) return;

        // If I sit on this lane
        if (y > seg.y1 && y < seg.y2) {
          // And I exist at the time of the link
          // use strict inequality for collision?
          // Link is at seg.time.
          // Chain is [start, end].
          // Collision if start <= time && end >= time (inclusive? or strict?)
          // checkCollision uses strict !(end < time || start > time)
          // i.e. start <= time && end >= time.
          // But specifically for blocking, we use the same rules.

          // Optimized inline check
          if (seg.time >= chain.startTime && seg.time <= chain.endTime) {
            // Check strict single-point overlap if needed?
            // If Node ends at 2000, Link at 2000. Strict inequality says NO collision.
            // So we should match checkCollision logic:
            // !(chain.end < seg.time || chain.start > seg.time)

            if (!(chain.endTime < seg.time || chain.startTime > seg.time)) {
              blockerCost += BLOCKER_PENALTY;
            }
          }
        }
      });

      // 4. Y-Shape Symmetry (Merge/Split Separation)
      // Goal: If I share a child/parent with another node, we should be 2 lanes apart
      // to let the common node sit in the middle.
      let yShapeCost = 0;
      const Y_SHAPE_PENALTY = LAYOUT_CONFIG.WEIGHTS.Y_SHAPE;

      // Check Spouses (Shared Child)
      childrenForAttraction.forEach(c => {
        // Who else parents this child?
        const spouses = chainParents.get(c.id) || [];
        spouses.forEach(spouse => {
          if (spouse.id === chain.id) return;
          // If spouse is too close (< 2 lanes)
          if (Math.abs(spouse.yIndex - y) < 2) {
            yShapeCost += Y_SHAPE_PENALTY;
          }
        });
      });

      // Check Siblings (Shared Parent)
      parents.forEach(p => {
        // Who else is a child of this parent?
        const siblings = chainChildren.get(p.id) || [];
        siblings.forEach(sib => {
          if (sib.id === chain.id) return; // Don't check against self
          // If sibling is too close (< 2 lanes)
          if (Math.abs(sib.yIndex - y) < 2) {
            yShapeCost += Y_SHAPE_PENALTY;
          }
        });
      });

      return attractionCost + cutThroughCost + blockerCost + yShapeCost;
    };

    for (let iter = 0; iter < ITERATIONS; iter++) {
      let energyChanged = false;

      // Rebuild segments at start of iteration
      rebuildSegments();

      // STRATEGY: Tri-State Alternating Iteration
      // 0 (Forward): Parents Push (Time ASC)
      // 1 (Backward): Children Pull (Time DESC)
      // 2 (Gravity): Hubs Anchor (Degree DESC) - Allows "Loose Ends" to snap to heavy Hubs
      const cycle = iter % 3;

      if (cycle === 0) {
        family.chains.sort((a, b) => a.startTime - b.startTime);
      } else if (cycle === 1) {
        family.chains.sort((a, b) => b.startTime - a.startTime);
      } else {
        // Cycle 2: Gravity Sort (Degree DESC)
        family.chains.sort((a, b) => {
          const degA = chainDegrees.get(a.id) || 0;
          const degB = chainDegrees.get(b.id) || 0;
          return degB - degA; // Highest connectivity first (Hubs)
        });
      }

      family.chains.forEach(chain => {
        const currentY = chain.yIndex;
        // Optimization: exclude my own links from verticalSegments? 

        // Calculate Base Cost
        let currentCost = calculateCost(chain, currentY);

        // Add "Lane Sharing / Stranger Danger" Penalty to Base Cost
        const getSharingPenalty = (y, myChain) => {
          const slots = ySlots.get(y);
          if (!slots || slots.length === 0) return 0;

          // If I share with someone, check if they are family.
          const parents = chainParents.get(myChain.id) || [];
          const children = chainChildren.get(myChain.id) || [];

          // Check every occupant
          let minGap = Infinity;
          let hasStranger = false;

          const BASE_SHARING_WEIGHT = LAYOUT_CONFIG.WEIGHTS.LANE_SHARING;

          for (const s of slots) {
            if (s.chainId === myChain.id) continue;

            const isParent = parents.some(p => p.id === s.chainId);
            const isChild = children.some(c => c.id === s.chainId);

            if (!isParent && !isChild) {
              hasStranger = true;

              // Calculate Gap
              const gap1 = myChain.startTime - s.end;
              const gap2 = s.start - myChain.endTime;

              const gap = Math.max(gap1, gap2);
              if (gap < minGap) minGap = gap;
            }
          }

          if (!hasStranger) return 0;

          // Distance-Based Decay
          // Formula: Cost = WEIGHT / Gap
          // Gap 1 (Tight): Cost ~500. (Repels > 2 lane attraction)
          // Gap 10 (Far): Cost ~50. (Attracts Pack)
          const safeGap = Math.max(0.5, minGap);
          return BASE_SHARING_WEIGHT / safeGap;
        };

        currentCost += getSharingPenalty(currentY, chain);

        // Explore wider neighborhood to jump over obstacles
        // Increased radius to escape deep blocks
        const SEARCH_RADIUS = LAYOUT_CONFIG.SEARCH_RADIUS;
        const candidates = new Set();

        // Add neighbors
        for (let i = 1; i <= SEARCH_RADIUS; i++) {
          candidates.add(currentY - i);
          candidates.add(currentY + i);
        }

        // Add parent target vicinity explicitly
        const parents = chainParents.get(chain.id) || [];
        if (parents.length > 0) {
          const avg = Math.round(parents.reduce((sum, p) => sum + p.yIndex, 0) / parents.length);
          // Search around the parent's average too! Parent itself might block 'avg', 
          // but 'avg+1' might be free and perfect.
          const TARGET_RADIUS = LAYOUT_CONFIG.TARGET_RADIUS;
          for (let k = 0; k <= TARGET_RADIUS; k++) {
            candidates.add(avg - k);
            candidates.add(avg + k);
          }
        }

        // Add child target vicinity
        const children = chainChildren.get(chain.id) || [];
        if (children.length > 0) {
          const avg = Math.round(children.reduce((sum, c) => sum + c.yIndex, 0) / children.length);
          const TARGET_RADIUS = LAYOUT_CONFIG.TARGET_RADIUS;
          for (let k = 0; k <= TARGET_RADIUS; k++) {
            candidates.add(avg - k);
            candidates.add(avg + k);
          }
        }

        let bestY = currentY;
        let bestCost = currentCost;

        candidates.forEach(y => {
          if (y < 0) return;
          if (y === currentY) return;

          // Check Hard Collision
          if (!checkCollision(y, chain.startTime, chain.endTime, chain.id)) {

            let cost = calculateCost(chain, y);
            // ADD SHARING PENALTY
            cost += getSharingPenalty(y, chain);

            if (cost < bestCost) {
              bestCost = cost;
              bestY = y;
            }
          }
        });

        if (bestY !== currentY) {
          // Apply Move
          const oldSlots = ySlots.get(currentY);
          const idx = oldSlots.findIndex(s => s.chainId === chain.id);
          if (idx !== -1) oldSlots.splice(idx, 1);

          occupySlot(bestY, chain);
          chain.yIndex = bestY;
          energyChanged = true;
        }
      });

      if (!energyChanged) break;
    }

    // 3. Post-Processing: Compaction
    // Remove empty lanes
    let maxLane = 0;
    ySlots.forEach((slots, y) => { if (slots.length > 0 && y > maxLane) maxLane = y; });

    for (let y = 0; y <= maxLane; y++) {
      // If lane y is empty (no slots or empty slots array)
      if (!ySlots.has(y) || ySlots.get(y).length === 0) {
        // Shift everything > y down by 1
        let shifted = false;
        for (let k = y + 1; k <= maxLane; k++) {
          if (ySlots.has(k)) {
            const slots = ySlots.get(k);
            ySlots.delete(k);
            ySlots.set(k - 1, slots);
            slots.forEach(s => {
              // Update chain object
              const c = family.chains.find(ch => ch.id === s.chainId);
              if (c) c.yIndex = k - 1;
            });
            shifted = true;
          }
        }
        if (shifted) {
          maxLane--;
          y--; // Re-check this index (now filled with k)
        }
      }
    }

    // Recalc maxY after moves
    maxY = 0;
    family.chains.forEach(c => { if (c.yIndex > maxY) maxY = c.yIndex; });

    return (maxY + 1) * this.rowHeight;
  }

  /**
   * Assign swimlane indices within a family using improved algorithm:
   * - Linear chains (single predecessor/successor) share the same lane if temporally compatible
   * - Splits/merges create Y-patterns with branches surrounding the common node
   * - Minimize link crossings by keeping related nodes close
   * - Priority: legal transfers over spiritual successions
   */
  assignSwimlanes(family, allNodes) {
    const assignments = {};
    const nodeMap = new Map(allNodes.map(n => [n.id, n]));

    // Build predecessor/successor maps with event types
    const predecessors = new Map(); // nodeId -> [{nodeId, type}]
    const successors = new Map();   // nodeId -> [{nodeId, type}]

    this.links.forEach(link => {
      if (family.includes(link.source) && family.includes(link.target)) {
        if (!predecessors.has(link.target)) predecessors.set(link.target, []);
        if (!successors.has(link.source)) successors.set(link.source, []);
        predecessors.get(link.target).push({ nodeId: link.source, type: link.type });
        successors.get(link.source).push({ nodeId: link.target, type: link.type });
      }
    });

    // Find the starting node (earliest founding year, or node with no predecessors)
    const rootNodes = family.filter(id => !predecessors.has(id) || predecessors.get(id).length === 0);
    let startNode;
    if (rootNodes.length > 0) {
      startNode = rootNodes.reduce((earliest, nodeId) => {
        const node = nodeMap.get(nodeId);
        const earliestNode = nodeMap.get(earliest);
        return (!earliestNode || node.founding_year < earliestNode.founding_year) ? nodeId : earliest;
      });
    } else {
      // Circular or complex graph - start with earliest founding year
      startNode = family.reduce((earliest, nodeId) => {
        const node = nodeMap.get(nodeId);
        const earliestNode = nodeMap.get(earliest);
        return (!earliestNode || node.founding_year < earliestNode.founding_year) ? nodeId : earliest;
      });
    }

    // Assign swimlanes using topological sort with crossing minimization
    const visited = new Set();
    let nextAvailableLane = 0;

    const assignNode = (nodeId, preferredLane) => {
      if (visited.has(nodeId)) return;
      visited.add(nodeId);

      // Check if this lane has temporal overlap - if so, push conflicting nodes down
      const finalLane = this.assignToLaneWithSpaceMaking(
        nodeId, preferredLane, assignments, nodeMap, family, visited
      );

      assignments[nodeId] = finalLane;

      const preds = predecessors.get(nodeId) || [];
      const succs = successors.get(nodeId) || [];

      // Try to use predecessor's lane to minimize crossings
      // Use the confirmed assignment of the current node as the baseline for successors
      // This ensures linear chains maintain their lane (e.g. in Splits or if shifted)
      let suggestedLane = assignments[nodeId];

      // Process successors
      if (succs.length === 0) {
        // Terminal node
        return;
      } else if (succs.length === 1) {
        // Linear chain - check temporal overlap
        const successor = succs[0];
        const currentNode = nodeMap.get(nodeId);
        const successorNode = nodeMap.get(successor.nodeId);

        const currentEnd = currentNode.dissolution_year || Infinity;
        const successorStart = successorNode.founding_year;
        const noTemporalOverlap = currentEnd < successorStart;

        if (noTemporalOverlap) {
          // No overlap - share lane with predecessor if possible
          // UNLESS it's a standard merge (multiple predecessors, no legal transfer priority),
          // in which case we force a Y-shape for symmetry.

          const isMergeTarget = predecessors.get(successor.nodeId)?.length > 1;
          const isLegalTransfer = successor.type === 'LEGAL_TRANSFER';

          if (isMergeTarget && !isLegalTransfer) {
            // Force offset for symmetry (this creates the first leg of the Y)
            // We use +1 as the default offset for the "main" predecessor
            assignNode(successor.nodeId, suggestedLane + 1);
          } else {
            assignNode(successor.nodeId, suggestedLane);
          }
        } else {
          // Temporal overlap - need different lane
          // Check if we can place it without increasing lane count too much
          const node = nodeMap.get(nodeId);
          const succNode = nodeMap.get(successor.nodeId);

          // Find the best alternative lane to minimize crossings
          // Prefer lanes closer to parent, but avoid temporal overlaps
          let bestLane = suggestedLane + 1;
          let minCrossings = Infinity;

          // Try a few lane options
          for (let offset = 1; offset <= 3; offset++) {
            const testLane = suggestedLane + offset;
            const crossings = this.estimateLinkCrossings(nodeId, successor.nodeId, testLane, assignments, nodeMap);
            if (crossings < minCrossings) {
              minCrossings = crossings;
              bestLane = testLane;
            }

            // Also try negative offset
            const negTestLane = suggestedLane - offset;
            const negCrossings = this.estimateLinkCrossings(nodeId, successor.nodeId, negTestLane, assignments, nodeMap);
            if (negCrossings < minCrossings) {
              minCrossings = negCrossings;
              bestLane = negTestLane;
            }
          }

          assignNode(successor.nodeId, bestLane);
        }
      } else {
        // Split: multiple successors
        const sortedSuccs = [...succs].sort((a, b) => {
          const priorityA = a.type === 'LEGAL_TRANSFER' ? 3 : a.type === 'SPIRITUAL_SUCCESSION' ? 2 : 1;
          const priorityB = b.type === 'LEGAL_TRANSFER' ? 3 : b.type === 'SPIRITUAL_SUCCESSION' ? 2 : 1;
          return priorityB - priorityA;
        });

        const currentNode = nodeMap.get(nodeId);
        const currentEnd = currentNode.dissolution_year || Infinity;

        // Check if we have a clear hierarchy (legal transfer as first, and it's unique)
        const hasLegalPriority = sortedSuccs[0].type === 'LEGAL_TRANSFER' &&
          (sortedSuccs.length === 1 || sortedSuccs[1].type !== 'LEGAL_TRANSFER');

        if (hasLegalPriority) {
          // Clear hierarchy: legal transfer gets priority
          const legalSucc = sortedSuccs[0];
          const legalNode = nodeMap.get(legalSucc.nodeId);
          const legalStart = legalNode.founding_year;
          const noOverlap = currentEnd < legalStart;

          // Legal transfer can share lane if no temporal overlap
          if (noOverlap) {
            assignNode(legalSucc.nodeId, suggestedLane);
          } else {
            // Temporal overlap - place slightly offset
            assignNode(legalSucc.nodeId, suggestedLane + 1);
          }

          // Place other branches in Y-pattern around the legal transfer
          const otherSuccs = sortedSuccs.slice(1);
          otherSuccs.forEach((succ, idx) => {
            const offset = Math.floor((idx + 1) / 2) * (idx % 2 === 0 ? 1 : -1);
            const branchLane = suggestedLane + offset * 2;
            assignNode(succ.nodeId, branchLane);
          });
        } else {
          // No clear priority - check temporal compatibility for ALL successors
          const compatibleSuccs = [];
          const incompatibleSuccs = [];

          sortedSuccs.forEach(succ => {
            const succNode = nodeMap.get(succ.nodeId);
            const succStart = succNode.founding_year;
            const noOverlap = currentEnd < succStart;

            if (noOverlap) {
              compatibleSuccs.push(succ);
            } else {
              incompatibleSuccs.push(succ);
            }
          });

          // If only one is temporally compatible, it can share the lane
          if (compatibleSuccs.length === 1 && incompatibleSuccs.length > 0) {
            assignNode(compatibleSuccs[0].nodeId, suggestedLane);

            // Others form Y-pattern
            incompatibleSuccs.forEach((succ, idx) => {
              const offset = Math.ceil((idx + 1) / 2) * (idx % 2 === 0 ? 1 : -1);
              const branchLane = suggestedLane + offset;
              assignNode(succ.nodeId, branchLane);
            });
          } else {
            // All compatible OR all incompatible OR multiple compatible: TRUE Y-SHAPE
            // Distribute all branches symmetrically away from parent
            sortedSuccs.forEach((succ, idx) => {
              const offset = Math.ceil((idx + 1) / 2) * (idx % 2 === 0 ? 1 : -1);
              const branchLane = suggestedLane + offset;
              assignNode(succ.nodeId, branchLane);
            });
          }
        }
      }
    };

    // Start assignment
    assignNode(startNode, 0);

    // Handle unvisited nodes
    // Handle unvisited nodes (e.g. the other legs of a merge)
    // "Smart Start": Place them symmetrically relative to their already-assigned successors
    family.forEach(nodeId => {
      if (!visited.has(nodeId)) {
        let startLane = nextAvailableLane + 1;

        // Check if this node merges into an already-assigned node
        const nodeSuccs = successors.get(nodeId) || [];
        const assignedSuccessor = nodeSuccs.find(s => visited.has(s.nodeId));

        if (assignedSuccessor) {
          const successorLane = assignments[assignedSuccessor.nodeId];
          const isStandardMerge = predecessors.get(assignedSuccessor.nodeId).length > 1 &&
            assignedSuccessor.type !== 'LEGAL_TRANSFER';

          if (isStandardMerge) {
            // Find a symmetric lane relative to the successor
            // We search in a radiating pattern: target-1, target+1, target-2, target+2...
            // skipping lanes that result in overlap.

            let foundLane = null;
            for (let offset = 1; offset <= 5; offset++) {
              // Try "above" (relative to target) first, then "below"
              // Because the first predecessor usually pushed target to +1, 
              // we expect target-1 to be taken by that first predecessor.
              // So we check: target+1 (Lane 2), target-1 (Lane 0 - likely taken), target+2...

              const candidates = [successorLane + offset, successorLane - offset];

              for (const candidate of candidates) {
                // Check if this lane is free for this node's duration
                const hasOverlap = this.hasTemporalOverlapInLane(nodeId, candidate, assignments, nodeMap, family);
                if (!hasOverlap) {
                  foundLane = candidate;
                  break;
                }
              }
              if (foundLane !== null) break;
            }

            if (foundLane !== null) {
              startLane = foundLane;
              // If use nextAvailableLane, don't increment it unnecessarily
              // But usually we want to reserve it? 
              // Actually if we pick a specific lane, we don't touch nextAvailableLane yet
              // unless startLane >= nextAvailableLane.
              if (startLane > nextAvailableLane) nextAvailableLane = startLane;
            } else {
              nextAvailableLane++;
              startLane = nextAvailableLane;
            }
          } else {
            nextAvailableLane++;
            startLane = nextAvailableLane;
          }
        } else {
          nextAvailableLane++;
          startLane = nextAvailableLane;
        }

        assignNode(nodeId, startLane);
      }
    });

    // Normalize lanes
    const usedLanes = Object.values(assignments);
    const minLane = Math.min(...usedLanes);
    const normalized = {};
    Object.entries(assignments).forEach(([nodeId, lane]) => {
      normalized[nodeId] = lane - minLane;
    });

    return normalized;
  }

  /**
   * Estimate how many links would cross if a node is placed in a given lane
   * Returns a heuristic value (lower is better)
   */
  estimateLinkCrossings(fromNodeId, toNodeId, testLane, assignments, nodeMap) {
    // Legacy method preserved for reference if needed, but unused by new algorithm.
    // Can be removed in future cleanup.
    return 0;
  }



  calculateLinkPaths(nodes) {
    // Create node position lookup
    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    const links = this.links.map(link => {
      const source = nodeMap.get(link.source);
      const target = nodeMap.get(link.target);

      if (!source || !target) {
        console.warn('Link references missing node:', link);
        return null;
      }

      // Check if nodes are on the same swimlane (within 5px tolerance)
      const sameSwimlane = Math.abs(source.y - target.y) < 5;

      // Viscous Connectors Implementation
      const pathData = this.generateLinkPath(source, target, link, sameSwimlane);

      const result = {
        ...link,
        sourceX: source.x + source.width,
        sourceY: source.y + source.height / 2,
        targetX: target.x,
        targetY: target.y + target.height / 2,
        sameSwimlane,
        path: pathData.d,
        debugPoints: pathData.debugPoints,
        topPathD: pathData.topPathD,
        bottomPathD: pathData.bottomPathD,
        bezierDebugPoints: pathData.bezierDebugPoints
      };

      // Debug log first few links
      if (this.links.indexOf(link) < 3) {
        const sourceName = source.eras?.[source.eras.length - 1]?.name || `Node ${link.source}`;
        const targetName = target.eras?.[0]?.name || `Node ${link.target}`;
        console.log(`Link ${link.source}->${link.target} (${sourceName}->${targetName}): sourceY=${source.y}, targetY=${target.y}, sameSwimlane=${sameSwimlane}`);
      }

      return result;
    }).filter(Boolean);

    console.log('calculateLinkPaths: regenerated', links.length, 'links with updated positions');
    return links;
  }

  generateLinkPath(source, target, link, sameSwimlane) {
    // Restore logic: same-swimlane transitions use markers (null path)
    if (sameSwimlane && link?.type !== 'MERGE' && link?.type !== 'SPLIT') {
      return { d: null, debugPoints: null, topPathD: null, bottomPathD: null };
    }

    // Viscous Connectors Implementation
    return this.generateViscousPath(source, target, link);
  }

  generateViscousPath(source, target, link) {
    // 1. Calculate Construction Points
    const sxEnd = source.x + source.width;
    const txStart = target.x;

    // Connector edges must be vertically aligned with the date of the connection.
    // That means: BOTH the source attachment edge and target attachment edge use the SAME X.
    // With the user-confirmed "vertical diameters" rule, this also ensures every semicircle
    // segment has a vertical diameter (p1.x === p2.x).
    let eventX = null;
    if (link?.year != null && this.xScale) {
      eventX = this.xScale(link.year);
    }

    // Fallback: if year is missing, use the midpoint between the two node edges, but still
    // force both endpoints onto the same vertical line so the arc-diameter rule holds.
    if (eventX == null) {
      eventX = (sxEnd + txStart) / 2;
    }

    // Clamp the attachment X into each node’s horizontal bounds (tiny tolerance), but keep
    // the two edges aligned by choosing a single clamped value that fits BOTH nodes.
    const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
    const sourceMinX = source.x - 1;
    const sourceMaxX = sxEnd + 1;
    const targetMinX = target.x - 1;
    const targetMaxX = (target.x + target.width) + 1;

    const sharedMinX = Math.max(sourceMinX, targetMinX);
    const sharedMaxX = Math.min(sourceMaxX, targetMaxX);

    // Prefer keeping the connector exactly on the event year, but guarantee it stays within
    // the shared feasible range if one exists.
    const spineX = (sharedMinX <= sharedMaxX)
      ? clamp(eventX, sharedMinX, sharedMaxX)
      : (clamp(eventX, sourceMinX, sourceMaxX) + clamp(eventX, targetMinX, targetMaxX)) / 2;

    const sy = source.y;
    const sh = source.height;
    const ty = target.y;
    const th = target.height;

    const st = { x: spineX, y: sy };
    const sb = { x: spineX, y: sy + sh };
    const tt = { x: spineX, y: ty };
    const tb = { x: spineX, y: ty + th };

    // Center Points (Waist)
    const midX = spineX;

    // Calculate vertical center of the "inner gap"
    let midY;
    if (sb.y <= tt.y) { // Source Above Target
      midY = (sb.y + tt.y) / 2;
    } else if (tb.y <= st.y) { // Source Below Target
      midY = (st.y + tb.y) / 2;
    } else { // Overlap
      midY = (sy + sh / 2 + ty + th / 2) / 2;
    }

    // Waist points - pinched (nearly coincident)
    // IMPORTANT: spec naming: cb = center bottom, ct = center top.
    // With SVG Y-down, that means: ct.y < cb.y.
    let pinch = 2;
    if (sb.y <= tt.y) {
      const gap = tt.y - sb.y;
      // Keep the pinch small and inside the gap, but never exactly 0.
      pinch = Math.max(0.01, Math.min(2, gap / 4));
      pinch = Math.min(pinch, Math.max(0.01, gap / 2 - 0.01));
    } else if (tb.y <= st.y) {
      const gap = st.y - tb.y;
      pinch = Math.max(0.01, Math.min(2, gap / 4));
      pinch = Math.min(pinch, Math.max(0.01, gap / 2 - 0.01));
    }

    const ct = { x: midX, y: midY - pinch }; // center top
    const cb = { x: midX, y: midY + pinch }; // center bottom

    // Save points to link for debug rendering
    const debugPoints = { st, sb, tt, tb, ct, cb };
    const bezierDebugPoints = [];
    let bezierPointIndex = 0; // unique ID for stable joins

    // 2. Generate Bézier helpers that mimic the previous semicircle arcs exactly.
    const waistCenterY = midY;
    const waistCenter = { x: spineX, y: waistCenterY };
    let quarterSequenceIndex = 0;

    const generateVerticalSemiCircle = (p1, p2, bulge /* 'right' | 'left' */) => {
      const dy = p2.y - p1.y;
      const absDy = Math.abs(dy);
      if (absDy < 0.1) {
        return `L ${p2.x} ${p2.y}`;
      }

      const radius = absDy / 2;
      const cx = p1.x;
      const cy = (p1.y + p2.y) / 2;

      const toMath = (pt) => ({ x: pt.x, y: -pt.y });
      const toSvg = (pt) => ({ x: pt.x, y: -pt.y });
      const format = (value) => Number(value.toFixed(3));

      const centerMath = toMath({ x: cx, y: cy });
      const startMath = toMath(p1);
      const endMath = toMath(p2);

      let startAngle = Math.atan2(startMath.y - centerMath.y, startMath.x - centerMath.x);
      let endAngle = Math.atan2(endMath.y - centerMath.y, endMath.x - centerMath.x);
      let delta = endAngle - startAngle;
      const movingDown = dy > 0;
      const desiredSign = bulge === 'right'
        ? (movingDown ? -1 : 1)
        : (movingDown ? 1 : -1);
      if (desiredSign > 0 && delta < 0) {
        delta += Math.PI * 2;
      } else if (desiredSign < 0 && delta > 0) {
        delta -= Math.PI * 2;
      }

      const maxStep = Math.PI / 2;
      const segments = Math.max(1, Math.ceil(Math.abs(delta) / maxStep));
      const step = delta / segments;
      let currentAngle = startAngle;
      let path = '';
      let overrideStartMath = null;

      for (let i = 0; i < segments; i++) {
        const p0IdealMath = {
          x: centerMath.x + radius * Math.cos(currentAngle),
          y: centerMath.y + radius * Math.sin(currentAngle)
        };
        let p0Math = overrideStartMath ?? p0IdealMath;
        overrideStartMath = null;
        const startDeltaX = p0Math.x - p0IdealMath.x;
        const startDeltaY = p0Math.y - p0IdealMath.y;

        const nextAngle = currentAngle + step;
        const t = (4 / 3) * Math.tan((nextAngle - currentAngle) / 4);

        const cosCurrent = Math.cos(currentAngle);
        const sinCurrent = Math.sin(currentAngle);
        const cosNext = Math.cos(nextAngle);
        const sinNext = Math.sin(nextAngle);

        let cp1Math = {
          x: centerMath.x + radius * cosCurrent - t * radius * sinCurrent,
          y: centerMath.y + radius * sinCurrent + t * radius * cosCurrent
        };
        cp1Math = {
          x: cp1Math.x + startDeltaX,
          y: cp1Math.y + startDeltaY
        };

        let p3Math = {
          x: centerMath.x + radius * cosNext,
          y: centerMath.y + radius * sinNext
        };
        let cp2Math = {
          x: centerMath.x + radius * cosNext + t * radius * sinNext,
          y: centerMath.y + radius * sinNext - t * radius * cosNext
        };

        if (i % 2 === 0) {
          let p3Screen = toSvg(p3Math);
          let cp2Screen = toSvg(cp2Math);
          const dirYSourceScreen = Math.sign(p1.y - waistCenterY);
          const dirYTargetScreen = Math.sign(p3Screen.y - waistCenterY);
          const awayDirYScreen = dirYTargetScreen !== 0 ? dirYTargetScreen : (dirYSourceScreen || 1);
          const shiftYScreen = awayDirYScreen * (radius / 3);
          const inwardDirXScreen = spineX - p3Screen.x;
          const shiftXScreen = Math.abs(inwardDirXScreen) < 1e-6 ? 0 : Math.sign(inwardDirXScreen) * ((2 * radius) / 5);
          p3Screen = {
            x: p3Screen.x + shiftXScreen,
            y: p3Screen.y + shiftYScreen
          };
          cp2Screen = {
            x: cp2Screen.x + shiftXScreen,
            y: cp2Screen.y + shiftYScreen
          };
          p3Math = toMath(p3Screen);
          cp2Math = toMath(cp2Screen);
        }

        const quarterOrdinal = quarterSequenceIndex++;
        if (quarterOrdinal % 4 === 0 || quarterOrdinal % 4 === 3) {
          const pullScreen = radius / 8;
          const adjustTowardCenter = (pointMath) => {
            const pointScreen = toSvg(pointMath);
            const deltaX = waistCenter.x - pointScreen.x;
            const deltaY = waistCenter.y - pointScreen.y;
            const shiftX = Math.abs(deltaX) < 1e-6 ? 0 : Math.sign(deltaX) * pullScreen;
            const shiftY = Math.abs(deltaY) < 1e-6 ? 0 : Math.sign(deltaY) * pullScreen;
            return toMath({
              x: pointScreen.x + shiftX,
              y: pointScreen.y + shiftY
            });
          };
          cp1Math = adjustTowardCenter(cp1Math);
          cp2Math = adjustTowardCenter(cp2Math);
        }

        const cp1 = toSvg(cp1Math);
        const cp2 = toSvg(cp2Math);
        const p3 = toSvg(p3Math);

        bezierDebugPoints.push({ x: format(cp1.x), y: format(cp1.y), role: 'cp', label: '0', segment: i, index: bezierPointIndex++ });
        bezierDebugPoints.push({ x: format(cp2.x), y: format(cp2.y), role: 'cp', label: '1', segment: i, index: bezierPointIndex++ });
        bezierDebugPoints.push({ x: format(p3.x), y: format(p3.y), role: 'anchor', label: '2', segment: i, index: bezierPointIndex++ });

        path += `C ${format(cp1.x)} ${format(cp1.y)} ${format(cp2.x)} ${format(cp2.y)} ${format(p3.x)} ${format(p3.y)} `;
        currentAngle = nextAngle;
        overrideStartMath = p3Math;
      }

      return path.trim();
    };

    // Construct boundary arcs
    // Top outline must be: st -> cb -> tt
    // Bottom outline must be: tb -> ct -> sb
    const a1 = generateVerticalSemiCircle(st, cb, 'right'); // D
    const a2 = generateVerticalSemiCircle(cb, tt, 'left');  // C
    const a4 = generateVerticalSemiCircle(tb, ct, 'left');  // C
    const a5 = generateVerticalSemiCircle(ct, sb, 'right'); // D

    const topPath = `${a1} ${a2}`;
    const bottomPath = `${a4} ${a5}`;

    // Store sub-paths for outline rendering
    const topPathD = `M ${st.x},${st.y} ${topPath}`;       // st->cb->tt
    const bottomPathD = `M ${tb.x},${tb.y} ${bottomPath}`; // tb->ct->sb

    // Full closed loop: fill strictly between the top and bottom outlines,
    // with straight vertical closures at the node attachment edges.
    const d = `M ${st.x},${st.y} ${a1} ${a2} L ${tb.x},${tb.y} ${a4} ${a5} L ${st.x},${st.y} Z`;

    return { d, debugPoints, topPathD, bottomPathD, bezierDebugPoints };
  }

  /**
   * Optimize swimlane assignments to minimize connector crossings.
   * Detects when a connector crosses intermediate nodes that exist during the connection timespan,
   * and tries swapping Y-shaped branch positions to eliminate crossings.
   */
  optimizeCrossings(family, assignments, allNodes) {
    const nodeMap = new Map(allNodes.map(n => [n.id, n]));

    // Build links within this family
    const familyLinks = this.links.filter(link =>
      family.includes(link.source) && family.includes(link.target)
    );

    // Find all split/merge points (nodes with multiple successors/predecessors)
    const predecessors = new Map();
    const successors = new Map();

    familyLinks.forEach(link => {
      if (!predecessors.has(link.target)) predecessors.set(link.target, []);
      if (!successors.has(link.source)) successors.set(link.source, []);
      predecessors.get(link.target).push({ nodeId: link.source, type: link.type, year: link.year });
      successors.get(link.source).push({ nodeId: link.target, type: link.type, year: link.year });
    });

    // Try swapping positions of Y-shaped branches to reduce crossings
    const optimized = { ...assignments };
    let improved = true;
    let iterations = 0;
    const maxIterations = 10;

    while (improved && iterations < maxIterations) {
      improved = false;
      iterations++;

      // For each node with multiple successors (splits)
      for (const [nodeId, succs] of successors.entries()) {
        if (succs.length < 2) continue;

        // Get successors in same relative position (Y-pattern branches)
        const branches = succs.map(s => s.nodeId);
        const parentLane = optimized[nodeId];

        // Try all permutations of branch positions
        const branchLanes = branches.map(b => optimized[b]);
        const uniqueBranchLanes = [...new Set(branchLanes)];

        if (uniqueBranchLanes.length < 2) continue; // All in same lane, nothing to swap

        // Count crossings for current arrangement
        const currentCrossings = this.countCrossingsForBranches(
          nodeId, branches, optimized, nodeMap, familyLinks
        );

        // Try swapping adjacent pairs
        for (let i = 0; i < branches.length - 1; i++) {
          for (let j = i + 1; j < branches.length; j++) {
            // Create test assignment with swapped lanes
            const testAssignments = { ...optimized };
            const temp = testAssignments[branches[i]];
            testAssignments[branches[i]] = testAssignments[branches[j]];
            testAssignments[branches[j]] = temp;

            // VALIDATE: Only accept swap if it doesn't create temporal overlaps
            if (this.swapCreatesOverlaps(branches[i], branches[j], optimized, testAssignments, nodeMap, family)) {
              continue; // Skip this swap
            }

            const testCrossings = this.countCrossingsForBranches(
              nodeId, branches, testAssignments, nodeMap, familyLinks
            );

            if (testCrossings < currentCrossings) {
              // Apply the swap
              optimized[branches[i]] = testAssignments[branches[i]];
              optimized[branches[j]] = testAssignments[branches[j]];
              improved = true;
            }
          }
        }
      }

      // For each node with multiple predecessors (merges)
      for (const [nodeId, preds] of predecessors.entries()) {
        if (preds.length < 2) continue;

        const branches = preds.map(p => p.nodeId);
        const targetLane = optimized[nodeId];

        // Count crossings for current arrangement
        const currentCrossings = this.countCrossingsForMerges(
          branches, nodeId, optimized, nodeMap, familyLinks
        );

        // Try swapping adjacent pairs
        for (let i = 0; i < branches.length - 1; i++) {
          for (let j = i + 1; j < branches.length; j++) {
            const testAssignments = { ...optimized };
            const temp = testAssignments[branches[i]];
            testAssignments[branches[i]] = testAssignments[branches[j]];
            testAssignments[branches[j]] = temp;

            // VALIDATE: Only accept swap if it doesn't create temporal overlaps
            if (this.swapCreatesOverlaps(branches[i], branches[j], optimized, testAssignments, nodeMap, family)) {
              continue; // Skip this swap
            }

            const testCrossings = this.countCrossingsForMerges(
              branches, nodeId, testAssignments, nodeMap, familyLinks
            );

            if (testCrossings < currentCrossings) {
              optimized[branches[i]] = testAssignments[branches[i]];
              optimized[branches[j]] = testAssignments[branches[j]];
              improved = true;
            }
          }
        }
      }
    }

    return optimized;
  }

  /**
   * Count connector crossings for split branches.
   * A crossing occurs when a connector from branch A to another node D crosses lane C,
   * where C contains a node that exists during the connection timespan.
   */
  countCrossingsForBranches(parentId, branches, assignments, nodeMap, familyLinks) {
    let crossings = 0;

    // For each branch, check all its outgoing connections
    branches.forEach(branchId => {
      const branchNode = nodeMap.get(branchId);
      const branchLane = assignments[branchId];

      // Find all links from this branch
      const outgoingLinks = familyLinks.filter(link => link.source === branchId);

      outgoingLinks.forEach(link => {
        const targetNode = nodeMap.get(link.target);
        const targetLane = assignments[link.target];

        if (targetLane === branchLane) return; // Same lane, no crossing

        // Connection goes from branchLane to targetLane
        const minLane = Math.min(branchLane, targetLane);
        const maxLane = Math.max(branchLane, targetLane);
        const connectionYear = link.year || targetNode.founding_year || branchNode.dissolution_year;

        // Check all intermediate lanes for nodes that exist during connection
        for (let lane = minLane + 1; lane < maxLane; lane++) {
          // Find nodes in this lane
          const nodesInLane = Array.from(nodeMap.values()).filter(n => assignments[n.id] === lane);

          nodesInLane.forEach(intermediateNode => {
            // Check if this node exists during the connection timespan
            const nodeStart = intermediateNode.founding_year;
            const nodeEnd = intermediateNode.dissolution_year || Infinity;

            if (connectionYear >= nodeStart && connectionYear <= nodeEnd) {
              crossings++;
            }
          });
        }
      });
    });

    return crossings;
  }

  /**
   * Count connector crossings for merge branches (similar to splits, but reversed).
   */
  countCrossingsForMerges(branches, targetId, assignments, nodeMap, familyLinks) {
    let crossings = 0;

    branches.forEach(branchId => {
      const branchNode = nodeMap.get(branchId);
      const branchLane = assignments[branchId];
      const targetLane = assignments[targetId];

      if (targetLane === branchLane) return;

      // Find the merge link
      const mergeLink = familyLinks.find(link => link.source === branchId && link.target === targetId);
      if (!mergeLink) return;

      const targetNode = nodeMap.get(targetId);
      const connectionYear = mergeLink.year || targetNode.founding_year || branchNode.dissolution_year;

      const minLane = Math.min(branchLane, targetLane);
      const maxLane = Math.max(branchLane, targetLane);

      for (let lane = minLane + 1; lane < maxLane; lane++) {
        const nodesInLane = Array.from(nodeMap.values()).filter(n => assignments[n.id] === lane);

        nodesInLane.forEach(intermediateNode => {
          const nodeStart = intermediateNode.founding_year;
          const nodeEnd = intermediateNode.dissolution_year || Infinity;

          if (connectionYear >= nodeStart && connectionYear <= nodeEnd) {
            crossings++;
          }
        });
      }
    });

    return crossings;
  }

  /**
   * Check if swapping two nodes would create temporal overlaps in their new lanes.
   * Returns true if the swap would create overlaps (meaning we should reject it).
   */
  swapCreatesOverlaps(nodeId1, nodeId2, currentAssignments, newAssignments, nodeMap, family) {
    const node1 = nodeMap.get(nodeId1);
    const node2 = nodeMap.get(nodeId2);

    const node1Start = node1.founding_year;
    const node1End = node1.dissolution_year || Infinity;
    const node2Start = node2.founding_year;
    const node2End = node2.dissolution_year || Infinity;

    const node1NewLane = newAssignments[nodeId1];
    const node2NewLane = newAssignments[nodeId2];

    // Check if node1 would overlap with any existing node in its new lane
    for (const otherId of family) {
      if (otherId === nodeId1 || otherId === nodeId2) continue;

      const otherLane = currentAssignments[otherId];

      // Check node1's new lane
      if (otherLane === node1NewLane) {
        const otherNode = nodeMap.get(otherId);
        const otherStart = otherNode.founding_year;
        const otherEnd = otherNode.dissolution_year || Infinity;

        // Check for temporal overlap: (start1 < end2) AND (start2 < end1)
        if (node1Start < otherEnd && otherStart < node1End) {
          return true; // Overlap detected
        }
      }

      // Check node2's new lane
      if (otherLane === node2NewLane) {
        const otherNode = nodeMap.get(otherId);
        const otherStart = otherNode.founding_year;
        const otherEnd = otherNode.dissolution_year || Infinity;

        // Check for temporal overlap
        if (node2Start < otherEnd && otherStart < node2End) {
          return true; // Overlap detected
        }
      }
    }

    return false; // No overlaps, swap is safe
  }

  /**
   * DEPRECATED: No longer needed - we now validate swaps before applying them
   * Resolve temporal overlaps in swimlanes.
   * After crossing optimization, nodes in the same lane might have temporal overlaps.
   * Move overlapping nodes to adjacent lanes.
   */
  resolveTemporalOverlaps(family, assignments, allNodes) {
    const nodeMap = new Map(allNodes.map(n => [n.id, n]));
    const resolved = { ...assignments };

    // Group nodes by lane
    const laneGroups = new Map();
    family.forEach(nodeId => {
      const lane = resolved[nodeId];
      if (!laneGroups.has(lane)) {
        laneGroups.set(lane, []);
      }
      laneGroups.get(lane).push(nodeId);
    });

    // For each lane, check for temporal overlaps
    laneGroups.forEach((nodeIds, lane) => {
      // Sort by founding year
      const sortedNodes = nodeIds
        .map(id => ({ id, node: nodeMap.get(id) }))
        .sort((a, b) => a.node.founding_year - b.node.founding_year);

      // Check consecutive pairs for overlap
      for (let i = 0; i < sortedNodes.length - 1; i++) {
        const current = sortedNodes[i];
        const next = sortedNodes[i + 1];

        const currentEnd = current.node.dissolution_year || Infinity;
        const nextStart = next.node.founding_year;

        // If they overlap, move the second one to an adjacent lane
        if (currentEnd >= nextStart) {
          // Find an available lane (try above and below current lane)
          let newLane = null;
          for (let offset = 1; offset <= 5; offset++) {
            const testLaneAbove = lane + offset;
            const testLaneBelow = lane - offset;

            // Check if this lane has space
            const nodesInAbove = family.filter(id => resolved[id] === testLaneAbove);
            const nodesInBelow = family.filter(id => resolved[id] === testLaneBelow);

            // Check if moving to this lane would create overlap
            const canUseAbove = !this.hasTemporalOverlapInLane(
              next.id, testLaneAbove, resolved, nodeMap, family
            );
            const canUseBelow = !this.hasTemporalOverlapInLane(
              next.id, testLaneBelow, resolved, nodeMap, family
            );

            if (canUseAbove) {
              newLane = testLaneAbove;
              break;
            } else if (canUseBelow) {
              newLane = testLaneBelow;
              break;
            }
          }

          if (newLane !== null) {
            resolved[next.id] = newLane;
            // Update the lane group for next iteration
            const currentLaneNodes = laneGroups.get(lane);
            const index = currentLaneNodes.indexOf(next.id);
            if (index > -1) {
              currentLaneNodes.splice(index, 1);
            }
            if (!laneGroups.has(newLane)) {
              laneGroups.set(newLane, []);
            }
            laneGroups.get(newLane).push(next.id);
          }
        }
      }
    });

    return resolved;
  }

  /**
   * Check if a node would have temporal overlap with existing nodes in a lane
   */
  hasTemporalOverlapInLane(nodeId, lane, assignments, nodeMap, family) {
    const node = nodeMap.get(nodeId);
    const nodeStart = node.founding_year;
    const nodeEnd = node.dissolution_year || Infinity;

    // Find all other nodes in this lane
    const nodesInLane = family.filter(id => id !== nodeId && assignments[id] === lane);

    for (const otherId of nodesInLane) {
      const otherNode = nodeMap.get(otherId);
      const otherStart = otherNode.founding_year;
      const otherEnd = otherNode.dissolution_year || Infinity;

      // Check for overlap: (start1 < end2) AND (start2 < end1)
      if (nodeStart < otherEnd && otherStart < nodeEnd) {
        return true;
      }
    }

    return false;
  }

  /**
   * Optimize swimlane assignments to minimize connector crossings.
   * Detects when a connector crosses intermediate nodes that exist during the connection timespan,
   * and tries swapping Y-shaped branch positions to eliminate crossings.
   */
  optimizeCrossings(family, assignments, allNodes) {
    const nodeMap = new Map(allNodes.map(n => [n.id, n]));

    // Build links within this family
    const familyLinks = this.links.filter(link =>
      family.includes(link.source) && family.includes(link.target)
    );

    // Find all split/merge points (nodes with multiple successors/predecessors)
    const predecessors = new Map();
    const successors = new Map();

    familyLinks.forEach(link => {
      if (!predecessors.has(link.target)) predecessors.set(link.target, []);
      if (!successors.has(link.source)) successors.set(link.source, []);
      predecessors.get(link.target).push({ nodeId: link.source, type: link.type, year: link.year });
      successors.get(link.source).push({ nodeId: link.target, type: link.type, year: link.year });
    });

    // Try swapping positions of Y-shaped branches to reduce crossings
    const optimized = { ...assignments };
    let improved = true;
    let iterations = 0;
    const maxIterations = 10;

    while (improved && iterations < maxIterations) {
      improved = false;
      iterations++;

      // For each node with multiple successors (splits)
      for (const [nodeId, succs] of successors.entries()) {
        if (succs.length < 2) continue;

        // Get successors in same relative position (Y-pattern branches)
        const branches = succs.map(s => s.nodeId);
        const parentLane = optimized[nodeId];

        // Try all permutations of branch positions
        const branchLanes = branches.map(b => optimized[b]);
        const uniqueBranchLanes = [...new Set(branchLanes)];

        if (uniqueBranchLanes.length < 2) continue; // All in same lane, nothing to swap

        // Count crossings for current arrangement
        const currentCrossings = this.countCrossingsForBranches(
          nodeId, branches, optimized, nodeMap, familyLinks
        );

        // Try swapping adjacent pairs
        for (let i = 0; i < branches.length - 1; i++) {
          for (let j = i + 1; j < branches.length; j++) {
            // Create test assignment with swapped lanes
            const testAssignments = { ...optimized };
            const temp = testAssignments[branches[i]];
            testAssignments[branches[i]] = testAssignments[branches[j]];
            testAssignments[branches[j]] = temp;

            // VALIDATE: Only accept swap if it doesn't create temporal overlaps
            if (this.swapCreatesOverlaps(branches[i], branches[j], optimized, testAssignments, nodeMap, family)) {
              continue; // Skip this swap
            }

            const testCrossings = this.countCrossingsForBranches(
              nodeId, branches, testAssignments, nodeMap, familyLinks
            );

            if (testCrossings < currentCrossings) {
              // Apply the swap
              optimized[branches[i]] = testAssignments[branches[i]];
              optimized[branches[j]] = testAssignments[branches[j]];
              improved = true;
            }
          }
        }
      }

      // For each node with multiple predecessors (merges)
      for (const [nodeId, preds] of predecessors.entries()) {
        if (preds.length < 2) continue;

        const branches = preds.map(p => p.nodeId);
        const targetLane = optimized[nodeId];

        // Count crossings for current arrangement
        const currentCrossings = this.countCrossingsForMerges(
          branches, nodeId, optimized, nodeMap, familyLinks
        );

        // Try swapping adjacent pairs
        for (let i = 0; i < branches.length - 1; i++) {
          for (let j = i + 1; j < branches.length; j++) {
            const testAssignments = { ...optimized };
            const temp = testAssignments[branches[i]];
            testAssignments[branches[i]] = testAssignments[branches[j]];
            testAssignments[branches[j]] = temp;

            // VALIDATE: Only accept swap if it doesn't create temporal overlaps
            if (this.swapCreatesOverlaps(branches[i], branches[j], optimized, testAssignments, nodeMap, family)) {
              continue; // Skip this swap
            }

            const testCrossings = this.countCrossingsForMerges(
              branches, nodeId, testAssignments, nodeMap, familyLinks
            );

            if (testCrossings < currentCrossings) {
              optimized[branches[i]] = testAssignments[branches[i]];
              optimized[branches[j]] = testAssignments[branches[j]];
              improved = true;
            }
          }
        }
      }
    }

    return optimized;
  }

  /**
   * Count connector crossings for split branches.
   * A crossing occurs when a connector from branch A to another node D crosses lane C,
   * where C contains a node that exists during the connection timespan.
   */
  countCrossingsForBranches(parentId, branches, assignments, nodeMap, familyLinks) {
    let crossings = 0;

    // For each branch, check all its outgoing connections
    branches.forEach(branchId => {
      const branchNode = nodeMap.get(branchId);
      const branchLane = assignments[branchId];

      // Find all links from this branch
      const outgoingLinks = familyLinks.filter(link => link.source === branchId);

      outgoingLinks.forEach(link => {
        const targetNode = nodeMap.get(link.target);
        const targetLane = assignments[link.target];

        if (targetLane === branchLane) return; // Same lane, no crossing

        // Connection goes from branchLane to targetLane
        const minLane = Math.min(branchLane, targetLane);
        const maxLane = Math.max(branchLane, targetLane);
        const connectionYear = link.year || targetNode.founding_year || branchNode.dissolution_year;

        // Check all intermediate lanes for nodes that exist during connection
        for (let lane = minLane + 1; lane < maxLane; lane++) {
          // Find nodes in this lane
          const nodesInLane = Array.from(nodeMap.values()).filter(n => assignments[n.id] === lane);

          nodesInLane.forEach(intermediateNode => {
            // Check if this node exists during the connection timespan
            const nodeStart = intermediateNode.founding_year;
            const nodeEnd = intermediateNode.dissolution_year || Infinity;

            if (connectionYear >= nodeStart && connectionYear <= nodeEnd) {
              crossings++;
            }
          });
        }
      });
    });

    return crossings;
  }

  /**
   * Count connector crossings for merge branches (similar to splits, but reversed).
   */
  countCrossingsForMerges(branches, targetId, assignments, nodeMap, familyLinks) {
    let crossings = 0;

    branches.forEach(branchId => {
      const branchNode = nodeMap.get(branchId);
      const branchLane = assignments[branchId];
      const targetLane = assignments[targetId];

      if (targetLane === branchLane) return;

      // Find the merge link
      const mergeLink = familyLinks.find(link => link.source === branchId && link.target === targetId);
      if (!mergeLink) return;

      const targetNode = nodeMap.get(targetId);
      const connectionYear = mergeLink.year || targetNode.founding_year || branchNode.dissolution_year;

      const minLane = Math.min(branchLane, targetLane);
      const maxLane = Math.max(branchLane, targetLane);

      for (let lane = minLane + 1; lane < maxLane; lane++) {
        const nodesInLane = Array.from(nodeMap.values()).filter(n => assignments[n.id] === lane);

        nodesInLane.forEach(intermediateNode => {
          const nodeStart = intermediateNode.founding_year;
          const nodeEnd = intermediateNode.dissolution_year || Infinity;

          if (connectionYear >= nodeStart && connectionYear <= nodeEnd) {
            crossings++;
          }
        });
      }
    });

    return crossings;
  }

  /**
   * Check if swapping two nodes would create temporal overlaps in their new lanes.
   * Returns true if the swap would create overlaps (meaning we should reject it).
   */
  swapCreatesOverlaps(nodeId1, nodeId2, currentAssignments, newAssignments, nodeMap, family) {
    const node1 = nodeMap.get(nodeId1);
    const node2 = nodeMap.get(nodeId2);

    const node1Start = node1.founding_year;
    const node1End = node1.dissolution_year || Infinity;
    const node2Start = node2.founding_year;
    const node2End = node2.dissolution_year || Infinity;

    const node1NewLane = newAssignments[nodeId1];
    const node2NewLane = newAssignments[nodeId2];

    // Check if node1 would overlap with any existing node in its new lane
    for (const otherId of family) {
      if (otherId === nodeId1 || otherId === nodeId2) continue;

      const otherLane = currentAssignments[otherId];

      // Check node1's new lane
      if (otherLane === node1NewLane) {
        const otherNode = nodeMap.get(otherId);
        const otherStart = otherNode.founding_year;
        const otherEnd = otherNode.dissolution_year || Infinity;

        // Check for temporal overlap: (start1 < end2) AND (start2 < end1)
        if (node1Start < otherEnd && otherStart < node1End) {
          return true; // Overlap detected
        }
      }

      // Check node2's new lane
      if (otherLane === node2NewLane) {
        const otherNode = nodeMap.get(otherId);
        const otherStart = otherNode.founding_year;
        const otherEnd = otherNode.dissolution_year || Infinity;

        // Check for temporal overlap
        if (node2Start < otherEnd && otherStart < node2End) {
          return true; // Overlap detected
        }
      }
    }

    return false; // No overlaps, swap is safe
  }

  /**
   * DEPRECATED: No longer needed - we now validate swaps before applying them
   * Resolve temporal overlaps in swimlanes.
   * After crossing optimization, nodes in the same lane might have temporal overlaps.
   * Move overlapping nodes to adjacent lanes.
   */
  resolveTemporalOverlaps(family, assignments, allNodes) {
    const nodeMap = new Map(allNodes.map(n => [n.id, n]));
    const resolved = { ...assignments };

    // Group nodes by lane
    const laneGroups = new Map();
    family.forEach(nodeId => {
      const lane = resolved[nodeId];
      if (!laneGroups.has(lane)) {
        laneGroups.set(lane, []);
      }
      laneGroups.get(lane).push(nodeId);
    });

    // For each lane, check for temporal overlaps
    laneGroups.forEach((nodeIds, lane) => {
      // Sort by founding year
      const sortedNodes = nodeIds
        .map(id => ({ id, node: nodeMap.get(id) }))
        .sort((a, b) => a.node.founding_year - b.node.founding_year);

      // Check consecutive pairs for overlap
      for (let i = 0; i < sortedNodes.length - 1; i++) {
        const current = sortedNodes[i];
        const next = sortedNodes[i + 1];

        const currentEnd = current.node.dissolution_year || Infinity;
        const nextStart = next.node.founding_year;

        // If they overlap, move the second one to an adjacent lane
        if (currentEnd >= nextStart) {
          // Find an available lane (try above and below current lane)
          let newLane = null;
          for (let offset = 1; offset <= 5; offset++) {
            const testLaneAbove = lane + offset;
            const testLaneBelow = lane - offset;

            // Check if this lane has space
            const nodesInAbove = family.filter(id => resolved[id] === testLaneAbove);
            const nodesInBelow = family.filter(id => resolved[id] === testLaneBelow);

            // Check if moving to this lane would create overlap
            const canUseAbove = !this.hasTemporalOverlapInLane(
              next.id, testLaneAbove, resolved, nodeMap, family
            );
            const canUseBelow = !this.hasTemporalOverlapInLane(
              next.id, testLaneBelow, resolved, nodeMap, family
            );

            if (canUseAbove) {
              newLane = testLaneAbove;
              break;
            } else if (canUseBelow) {
              newLane = testLaneBelow;
              break;
            }
          }

          if (newLane !== null) {
            resolved[next.id] = newLane;
            // Update the lane group for next iteration
            const currentLaneNodes = laneGroups.get(lane);
            const index = currentLaneNodes.indexOf(next.id);
            if (index > -1) {
              currentLaneNodes.splice(index, 1);
            }
            if (!laneGroups.has(newLane)) {
              laneGroups.set(newLane, []);
            }
            laneGroups.get(newLane).push(next.id);
          }
        }
      }
    });

    return resolved;
  }

  /**
   * Check if a node would have temporal overlap with existing nodes in a lane
   */
  hasTemporalOverlapInLane(nodeId, lane, assignments, nodeMap, family) {
    const node = nodeMap.get(nodeId);
    const nodeStart = node.founding_year;
    const nodeEnd = node.dissolution_year || Infinity;

    // Find all other nodes in this lane
    const nodesInLane = family.filter(id => id !== nodeId && assignments[id] === lane);

    for (const otherId of nodesInLane) {
      const otherNode = nodeMap.get(otherId);
      const otherStart = otherNode.founding_year;
      const otherEnd = otherNode.dissolution_year || Infinity;

      // Check for overlap: (start1 < end2) AND (start2 < end1)
      if (nodeStart < otherEnd && otherStart < nodeEnd) {
        return true;
      }
    }

    return false;
  }
}
