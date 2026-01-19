import { VISUALIZATION } from '../constants/visualization';
import { LAYOUT_CONFIG } from './layout/config.js';
import { calculateYearRange, createXScale } from './layout/utils/scales.js';
import { checkCollision as checkCollisionUtil } from './layout/utils/collisionDetection.js';
import { generateVerticalSegments } from './layout/utils/verticalSegments.js';
import { calculateSingleChainCost, calculateCostDelta, getAffectedChains } from './layout/utils/costCalculator.js';
import { buildFamilies } from './layout/utils/chainBuilder.js';
import { runGreedyPass } from './layout/simplifiers/greedyOptimizer.js';
import { runGroupwiseOptimization } from './layout/simplifiers/groupwiseOptimizer.js';

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
    this.yearRange = calculateYearRange(this.nodes);
    this.xScale = createXScale(this.width, this.yearRange, this.stretchFactor);

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

      // ALSO: Check for VISUAL overlap with the single parent.
      // Since nodes render to dissolution_year + 1, we must check visual boundaries.
      // If parent visually extends into my start year, we overlap and must break the chain.
      const parentNode = nodeMap.get(parentId);
      const myNode = nodeMap.get(nodeId);

      let parentEnd = parentNode.dissolution_year;
      if (!parentEnd) {
        const lastEra = parentNode.eras?.[parentNode.eras.length - 1];
        parentEnd = lastEra ? lastEra.year : parentNode.founding_year;
      }

      // Visual overlap check: parent renders to (parentEnd + 1), so check if that > myStart
      // Example: Parent ends 2009 (renders to 2010), Child starts 2010 → 2010 > 2010 = FALSE (no overlap, can chain)
      // Example: Parent ends 2009 (renders to 2010), Child starts 2009 → 2010 > 2009 = TRUE (overlap, must break)
      if (parentEnd + 1 > myNode.founding_year) return true; // Visual overlap, break chain

      return false; // No visual overlap, can continue chain
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
          // CRITICAL: Check for VISUAL overlap (Dirty Data Protection)
          // Since nodes render to dissolution_year + 1, we must check visual boundaries.
          // If curr visually extends into next's start year, they overlap and must break.
          const currNode = nodeMap.get(curr);
          const nextNode = nodeMap.get(nextId);

          let currEnd = currNode.dissolution_year;
          if (!currEnd) {
            const lastEra = currNode.eras?.[currNode.eras.length - 1];
            currEnd = lastEra ? lastEra.year : currNode.founding_year;
          }

          // Visual overlap check: curr renders to (currEnd + 1), so check if that > nextStart
          // Example: Curr ends 2009 (renders to 2010), Next starts 2010 → 2010 > 2010 = FALSE (no overlap, continue)
          // Example: Curr ends 2009 (renders to 2010), Next starts 2009 → 2010 > 2009 = TRUE (overlap, break)
          if (currEnd + 1 > nextNode.founding_year) {
            // Visual overlap detected - break chain
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
    return buildFamilies(chains, this.links);
  }

  // getAffectedChains removed - moved to costCalculator.js

  /**
   * Calculates the total cost of all chains in a family.
   */
  // calculateGlobalCost removed - logic moved/refactored

  /**
   * Calculates the net change in global cost if a chain moves from oldY to newY.
   */
  // calculateCostDelta removed - moved to costCalculator.js

  /**
   * Internal helper for Slice 1 & 2 to calculate cost of a single chain.
   * This is a lift of the layoutFamily.calculateCost logic.
   */
  /**
   * Internal helper for Slice 1 & 2 to calculate cost of a single chain.
   * This is a lift of the layoutFamily.calculateCost logic.
   */
  _calculateSingleChainCost(chain, y, chainParents, chainChildren, verticalSegments, checkCollision) {
    return calculateSingleChainCost(chain, y, chainParents, chainChildren, verticalSegments, checkCollision);
  }

  layoutFamily(family) {
    if (family.chains.length === 0) return 0;

    // 1. Initial Placement (Topological / Barycenter guess)
    // Sort chains by start time to process legal parents first
    family.chains.sort((a, b) => a.startTime - b.startTime);

    const ySlots = new Map(); // yIndex -> Array of {start, end, chainId}
    let maxY = 0;

    // Collision check wrapper using extracted utility
    // Moved definition down to where it is used or after dependencies are initialized
    // to avoid TDZ if called early, though here it's passed as a callback.
    // Effectively we will define it before usage.


    const occupySlot = (y, chain) => {
      if (!ySlots.has(y)) ySlots.set(y, []);
      ySlots.get(y).push({ start: chain.startTime, end: chain.endTime, chainId: chain.id });
      chain.yIndex = y;
      if (y > maxY) maxY = y;
    };

    // Calculate parents and children maps for forces and collision detection
    // chainId -> [parentChainId, ...]
    const chainParents = new Map();
    const chainChildren = new Map();
    const nodeToChain = new Map();
    family.chains.forEach(c => {
      c.nodes.forEach(n => nodeToChain.set(n.id, c));
      chainChildren.set(c.id, []);
    });

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

    // Populate children map
    family.chains.forEach(child => {
      const parents = chainParents.get(child.id) || [];
      parents.forEach(p => {
        chainChildren.get(p.id).push(child);
      });
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
    // Wrapper for family-aware collision check using extracted utility
    // We define it here where dependencies (chainParents, etc.) are available.
    const checkCollision = (y, start, end, excludeChainId, movingChain) =>
      checkCollisionUtil(y, start, end, excludeChainId, movingChain, ySlots, family, chainParents, chainChildren);

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
        if (candidate >= 0 && !checkCollision(candidate, chain.startTime, chain.endTime, chain.id, chain)) {
          occupySlot(candidate, chain);
          placed = true;
          break;
        }
        if (offset > 0) {
          candidate = targetY - offset;
          if (candidate >= 0 && !checkCollision(candidate, chain.startTime, chain.endTime, chain.id, chain)) {
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
      ));

    // Calculate Degree (Connectivity) for Gravity Sort
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
      });
    });

    // Pre-calculate all active vertical segments to optimize "Blocker Penalty"
    // List of { y1, y2, time, childId, parentId }
    // Slice 8A: Configurable Pass Orchestrator
    // Replaces fixed Tri-State loop
    this._executePassSchedule(
      family, family.chains, chainParents, chainChildren,
      [], // verticalSegments are rebuilt internally per pass
      checkCollision, ySlots
    );


    // 3. Post-Processing: Normalization & Compaction

    // Normalize Y indices (Shift so min Y is 0)
    let minY = 0;
    family.chains.forEach(c => { if (c.yIndex < minY) minY = c.yIndex; });

    if (minY < 0) {
      const shift = -minY;
      ySlots.clear();
      maxY = 0; // Reset maxY tracking
      family.chains.forEach(c => {
        // occupySlot updates chain.yIndex and ySlots and maxY
        // But wait, occupySlot pushes to array.
        // We must manually update chain.yIndex first? 
        // Helper occupySlot: 
        //   ySlots.get(y).push(...)
        //   chain.yIndex = y;
        // So we just call occupySlot with new Y.
        occupySlot(c.yIndex + shift, c);
      });
    }

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
    if (sameSwimlane) {
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

        // Check for temporal overlap: (start1 <= end2) AND (start2 <= end1)
        if (node1Start <= otherEnd && otherStart <= node1End) {
          return true; // Overlap detected
        }
      }

      // Check node2's new lane
      if (otherLane === node2NewLane) {
        const otherNode = nodeMap.get(otherId);
        const otherStart = otherNode.founding_year;
        const otherEnd = otherNode.dissolution_year || Infinity;

        // Check for temporal overlap
        if (node2Start <= otherEnd && otherStart <= node2End) {
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

      // Check for overlap: (start1 <= end2) AND (start2 <= end1)
      // Uses inclusive comparison to match visual rendering
      if (nodeStart <= otherEnd && otherStart <= nodeEnd) {
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

        // Check for temporal overlap: (start1 <= end2) AND (start2 <= end1)
        if (node1Start <= otherEnd && otherStart <= node1End) {
          return true; // Overlap detected
        }
      }

      // Check node2's new lane
      if (otherLane === node2NewLane) {
        const otherNode = nodeMap.get(otherId);
        const otherStart = otherNode.founding_year;
        const otherEnd = otherNode.dissolution_year || Infinity;

        // Check for temporal overlap
        if (node2Start <= otherEnd && otherStart <= node2End) {
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



  // Slice 8A: Configurable Pass Orchestrator Helpers

  _executePassSchedule(family, chains, chainParents, chainChildren, unusedVs, checkCollision, ySlots, scheduleOverride = null) {
    const schedule = scheduleOverride || LAYOUT_CONFIG.PASS_SCHEDULE;

    // Calculate family metrics
    const familySize = chains.length || 0;
    let linkCount = 0;
    chains.forEach(c => {
      linkCount += (chainParents.get(c.id)?.length || 0);
      linkCount += (chainChildren.get(c.id)?.length || 0);
    });
    linkCount = linkCount / 2; // undirected edges

    let globalPassIndex = 0;

    for (const pass of schedule) {
      if (!this._shouldApplyPass(familySize, linkCount, pass)) continue;

      for (let i = 0; i < pass.iterations; i++) {
        for (const strategy of pass.strategies) {
          // Rebuild vertical segments for accurate blocker calculation
          const verticalSegments = generateVerticalSegments(chains, chainParents);

          if (strategy === 'HYBRID') {
            runGroupwiseOptimization(chains, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);
          } else {
            runGreedyPass(family, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots, strategy);
          }

          // Slice 8B: Log metrics
          this._logScore(globalPassIndex++, family, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);
        }
      }
    }
  }

  _shouldApplyPass(familySize, linkCount, passConfig) {
    if (familySize < (passConfig.minFamilySize || 0)) return false;
    if (linkCount < (passConfig.minLinks || 0)) return false;
    return true;
  }






  // Slice 8B: Layout Scoreboard
  _logScore(passIndex, family, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots) {
    if (!LAYOUT_CONFIG.SCOREBOARD.ENABLED) return;

    const metrics = this._calculateScore(family, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);

    // Use injected logger if available (safe for browser/node separation)
    if (typeof LAYOUT_CONFIG.SCOREBOARD.LOG_FUNCTION === 'function') {
      LAYOUT_CONFIG.SCOREBOARD.LOG_FUNCTION(passIndex, metrics);
    }
  }

  _calculateScore(family, chainParents, chainChildren, verticalSegments, checkCollision, ySlots) {
    let totalCost = 0;

    family.forEach(chain => {
      totalCost += this._calculateSingleChainCost(chain, chain.yIndex, chainParents, chainChildren, verticalSegments, checkCollision);
    });

    return {
      totalCost,
      crossings: 0,
      vacantLanes: ySlots.size,
      familySplay: 0
    };
  }
}
