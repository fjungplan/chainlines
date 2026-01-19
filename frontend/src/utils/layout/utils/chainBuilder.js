/**
 * Chain Builder Utilities
 * Responsible for grouping chains into disconnected subgraphs (families)
 * and preparing them for independent layout processing.
 */

/**
 * Group chains into connected components (families) based on links between nodes.
 * 
 * @param {Array<Object>} chains - Array of chain objects
 * @param {Array<Object>} links - Array of link objects {source: nodeId, target: nodeId}
 * @returns {Array<Object>} list of families { chains: [], minStart: number }
 */
export function buildFamilies(chains, links) {
    // Group chains into connected components
    const chainMap = new Map(); // nodeId -> chainId
    chains.forEach(c => c.nodes.forEach(n => chainMap.set(n.id, c)));

    const adj = new Map();
    chains.forEach(c => adj.set(c, new Set()));

    links.forEach(l => {
        // Logic from LayoutCalculator:
        // Nodes are referenced by ID in links.
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
