import { VISUALIZATION } from '../constants/visualization';
import { LAYOUT_CONFIG } from './layout/config.js';
import { calculateYearRange, createXScale } from './layout/utils/scales.js';
import { checkCollision as checkCollisionUtil } from './layout/utils/collisionDetection.js';
import { generateVerticalSegments } from './layout/utils/verticalSegments.js';
import { calculateSingleChainCost, calculateCostDelta, getAffectedChains } from './layout/utils/costCalculator.js';
import { buildFamilies, buildChains } from './layout/utils/chainBuilder.js';
import { executePassSchedule } from './layout/orchestrator/layoutOrchestrator.js';
import { Scoreboard } from './layout/analytics/layoutScoreboard.js';

/**
 * Calculate positions for all nodes using Sankey-like layout.
 * Acts as the main coordinator for the layout process, delegating specific
 * logic to specialized modules:
 * - ChainBuilder: Constructs lineage chains from raw nodes
 * - LayoutOrchestrator: Manages optimization passes
 * - Scoreboard: Tracks layout quality metrics
 * - GroupwiseOptimizer: Handles vertical placement optimization
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

    this.scoreboard = new Scoreboard();

    // Initialize precomputed layouts cache
    this.precomputedLayouts = null;
    this.loadPrecomputedLayouts(); // Async, non-blocking
  }

  async loadPrecomputedLayouts() {
    try {
      const response = await fetch('/api/v1/precomputed-layouts');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      this.precomputedLayouts = await response.json();
      console.log('✅ Loaded', Object.keys(this.precomputedLayouts).length, 'precomputed layouts');
    } catch (e) {
      console.warn('⚠️ No precomputed layouts available:', e.message);
      this.precomputedLayouts = {};
    }
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
    return buildChains(nodes, links);
  }
  buildFamilies(chains) {
    return buildFamilies(chains, this.links);
  }


  _calculateSingleChainCost(chain, y, chainParents, chainChildren, verticalSegments, checkCollision) {
    return calculateSingleChainCost(chain, y, chainParents, chainChildren, verticalSegments, checkCollision);
  }

  layoutFamily(family) {
    // Check if this is a complex family that might benefit from precomputed layouts
    if (this.isComplexFamily(family)) {
      const hash = this.computeFamilyHash(family);
      const cached = this.precomputedLayouts?.[hash];

      if (cached) {
        console.log('🎯 Using precomputed layout for family hash:', hash.substring(0, 16) + '...');
        return this.applyPrecomputedLayout(family, cached);
      }
    }

    // Fallback to dynamic algorithm
    return this.layoutFamilyDynamic(family);
  }

  isComplexFamily(family) {
    const chainCount = family.chains.length;
    const linkCount = this.countFamilyLinks(family);
    return chainCount >= 20 && linkCount > chainCount;
  }

  computeFamilyHash(family) {
    // Extract all node IDs from the family and sort them
    const nodeIds = family.chains
      .flatMap(c => c.nodes.map(n => n.id))
      .sort();
    return nodeIds.join(',');
  }

  applyPrecomputedLayout(family, cached) {
    // Apply the cached yIndex values to each chain
    family.chains.forEach(chain => {
      // The layout_data maps chain IDs (which are node IDs) to yIndex values
      const firstNodeId = chain.nodes[0]?.id;
      if (firstNodeId && cached.layout_data[firstNodeId] !== undefined) {
        chain.yIndex = cached.layout_data[firstNodeId];
      } else {
        // Fallback: try to find any node in this chain
        for (const node of chain.nodes) {
          if (cached.layout_data[node.id] !== undefined) {
            chain.yIndex = cached.layout_data[node.id];
            break;
          }
        }
      }
    });

    const maxY = Math.max(...family.chains.map(c => c.yIndex || 0));
    return (maxY + 1) * this.rowHeight;
  }

  countFamilyLinks(family) {
    const nodeIds = new Set(
      family.chains.flatMap(c => c.nodes.map(n => n.id))
    );
    return this.links.filter(l =>
      nodeIds.has(l.source) && nodeIds.has(l.target)
    ).length;
  }

  layoutFamilyDynamic(family) {
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



  // Slice 8A: Configurable Pass Orchestrator Helpers

  _executePassSchedule(family, chains, chainParents, chainChildren, unusedVs, checkCollision, ySlots, scheduleOverride = null) {
    executePassSchedule(
      family,
      chains,
      chainParents,
      chainChildren,
      unusedVs,
      checkCollision,
      ySlots,
      this.scoreboard.logScore.bind(this.scoreboard),
      scheduleOverride
    );
  }
}
