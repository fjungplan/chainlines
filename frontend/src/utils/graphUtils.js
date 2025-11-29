/**
 * Validate graph data structure for D3
 */
export function validateGraphData(data) {
  if (!data || !data.nodes || !data.links) {
    throw new Error('Invalid graph data: missing nodes or links');
  }
  
  const nodeIds = new Set(data.nodes.map(n => n.id));
  
  // Validate all links reference existing nodes
  for (const link of data.links) {
    if (!nodeIds.has(link.source)) {
      throw new Error(`Link references non-existent source: ${link.source}`);
    }
    if (!nodeIds.has(link.target)) {
      throw new Error(`Link references non-existent target: ${link.target}`);
    }
  }
  
  return true;
}

/**
 * Calculate graph bounds
 */
export function getGraphBounds(nodes) {
  const years = nodes.flatMap(n => 
    n.eras.map(e => e.year)
  );
  
  return {
    minYear: Math.min(...years),
    maxYear: Math.max(...years),
    nodeCount: nodes.length
  };
}
