import { VISUALIZATION } from '../constants/visualization';

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
    const nodesWithXY = this.assignYPositions(nodesWithX);
    
    // Step 3: Calculate link paths
    const linkPaths = this.calculateLinkPaths(nodesWithXY);
    
    return {
      nodes: nodesWithXY,
      links: linkPaths,
      yearRange: this.yearRange,
      xScale: this.xScale
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
      console.log(`${teamName}: [${node.founding_year}-${node.dissolution_year}] startX=${startX.toFixed(2)}, endX(${node.dissolution_year+1})=${endX.toFixed(2)}, width=${scaledWidth.toFixed(2)}`);
      // DON'T apply MIN_NODE_WIDTH for dissolved teams - keep accurate year boundaries
      return scaledWidth;
    } else {
      // Active: extend to end of yearRange (already includes +1 from filterYearRange)
      endX = this.xScale(this.yearRange.max);
      const scaledWidth = endX - startX;
      console.log(`${teamName}: [${node.founding_year}-active] startX=${startX.toFixed(2)}, endX(${this.yearRange.max})=${endX.toFixed(2)}, width=${scaledWidth.toFixed(2)}`);
      // For active teams, apply MIN_NODE_WIDTH if needed
      return Math.max(VISUALIZATION.MIN_NODE_WIDTH, scaledWidth);
    }
  }
  
  assignYPositions(nodes) {
    // Build lineage chains: each node gets its own swimlane unless it's in a direct succession chain
    const linkMap = new Map();
    this.links.forEach(link => {
      if (!linkMap.has(link.source)) linkMap.set(link.source, []);
      linkMap.get(link.source).push(link.target);
    });
    
    // Find all chains (sequences of connected nodes)
    const visited = new Set();
    const chains = [];
    
    const buildChain = (nodeId) => {
      const chain = [];
      let current = nodeId;
      
      // Walk backwards to find chain start
      const reverseMap = new Map();
      this.links.forEach(link => {
        if (!reverseMap.has(link.target)) reverseMap.set(link.target, []);
        reverseMap.get(link.target).push(link.source);
      });
      
      while (reverseMap.has(current) && reverseMap.get(current).length === 1) {
        const prev = reverseMap.get(current)[0];
        if (visited.has(prev)) break;
        current = prev;
      }
      
      // Walk forwards from start
      chain.push(current);
      visited.add(current);
      
      while (linkMap.has(current) && linkMap.get(current).length === 1) {
        const next = linkMap.get(current)[0];
        if (visited.has(next)) break;
        chain.push(next);
        visited.add(next);
        current = next;
      }
      
      return chain;
    };
    
    // Build all chains
    nodes.forEach(node => {
      if (!visited.has(node.id)) {
        const chain = buildChain(node.id);
        chains.push(chain);
      }
    });
    
    // Assign each chain to a swimlane
    const rowHeight = VISUALIZATION.NODE_HEIGHT + 20;
    const positioned = [];
    const nodePositions = new Map();
    
    chains.forEach((chain, swimlaneIndex) => {
      const y = 50 + swimlaneIndex * rowHeight;
      
      chain.forEach(nodeId => {
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          nodePositions.set(nodeId, {
            ...node,
            y,
            height: VISUALIZATION.NODE_HEIGHT
          });
          positioned.push(nodePositions.get(nodeId));
        }
      });
    });
    
    return positioned;
  }
  
  groupNodesByTier(nodes) {
    // Group nodes by their most common tier level
    const tierMap = new Map();
    
    nodes.forEach(node => {
      const tiers = node.eras.map(e => e.tier).filter(t => t);
      const avgTier = tiers.length > 0 
        ? Math.round(tiers.reduce((a, b) => a + b) / tiers.length)
        : 2; // Default to ProTeam
      
      if (!tierMap.has(avgTier)) {
        tierMap.set(avgTier, []);
      }
      tierMap.get(avgTier).push(node);
    });
    
    // Sort tiers (1 = WorldTour at top)
    return Array.from(tierMap.entries())
      .sort(([a], [b]) => a - b)
      .map(([_, nodes]) => nodes);
  }
  
  calculateLinkPaths(nodes) {
    // Create node position lookup
    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    
    return this.links.map(link => {
      const source = nodeMap.get(link.source);
      const target = nodeMap.get(link.target);
      
      if (!source || !target) {
        console.warn('Link references missing node:', link);
        return null;
      }
      
      return {
        ...link,
        sourceX: source.x + source.width,
        sourceY: source.y + source.height / 2,
        targetX: target.x,
        targetY: target.y + target.height / 2,
        path: this.generateLinkPath(source, target)
      };
    }).filter(Boolean);
  }
  
  generateLinkPath(source, target) {
    const sx = source.x + source.width;
    const sy = source.y + source.height / 2;
    const tx = target.x;
    const ty = target.y + target.height / 2;
    
    // Cubic Bezier curve
    const dx = tx - sx;
    const controlPointOffset = Math.abs(dx) * 0.3;
    
    return `M ${sx},${sy} 
            C ${sx + controlPointOffset},${sy} 
              ${tx - controlPointOffset},${ty} 
              ${tx},${ty}`;
  }
}
