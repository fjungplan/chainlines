/**
 * Chain Builder Utilities
 * Responsible for grouping chains into disconnected subgraphs (families)
 * and preparing them for independent layout processing.
 */

/**
 * Decomposes the list of nodes into linear "chains" (sequences of nodes).
 * A chain is formed when nodes have 1:1 predecessor/successor relationships
 * and no visual overlap logic violations.
 * 
 * @param {Array<Object>} nodes - All nodes
 * @param {Array<Object>} links - All links
 * @returns {Array<Object>} List of chain objects
 */
export function buildChains(nodes, links) {
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

    // Link Map for fast lookup of {source, target} -> link year
    const linkMap = new Map();
    links.forEach(l => linkMap.set(`${l.source}-${l.target}`, l.year || l.event_year));

    // Helper: Is this a "Primary Continuation" based on time?
    // Matches backend logic: abs(linkYear - childStart) <= 1
    const isPrimaryContinuation = (parentId, childId) => {
        const linkYear = linkMap.get(`${parentId}-${childId}`);
        const childNode = nodeMap.get(childId);
        if (linkYear === undefined || !childNode) return false;

        // Tolerance: +/- 1 year
        return Math.abs(linkYear - childNode.founding_year) <= 1;
    };

    const currentYear = new Date().getFullYear();

    const getEndYear = (node) => {
        if (node.dissolution_year) {
            return node.dissolution_year;
        }
        // Zombie Node Check: If no dissolution but has eras, use the last era
        const eras = node.eras || [];
        if (eras.length > 0) {
            const maxEraYear = Math.max(...eras.map(e => e.year || 0));
            if (maxEraYear > 0) return maxEraYear;
        }
        return currentYear;
    };

    // Helper: Get all primary predecessors for a node
    const getPrimaryPredecessors = (nodeId) => {
        const p = preds.get(nodeId) || [];
        return p.filter(parentId => isPrimaryContinuation(parentId, nodeId));
    };

    // 1. Identification of "Chain Starter" nodes
    const isChainStart = (nodeId) => {
        const p = preds.get(nodeId) || [];

        // Case 1: No Predecessors -> Start
        if (p.length === 0) return true;

        // Case 2: Multiple Predecessors (Merge)
        if (p.length > 1) {
            // CHECK PRIORITY: If there is EXACTLY ONE primary predecessor,
            // we do NOT start a chain (we let the primary parent continue).
            const primaryPreds = getPrimaryPredecessors(nodeId);
            if (primaryPreds.length === 1) return false;
            return true; // Ambiguous or None -> Start new chain
        }

        // Case 3: Single Predecessor
        const parentId = p[0];
        const parentSuccs = succs.get(parentId) || [];

        // Parent has multiple successors (Split) -> Start new chain
        if (parentSuccs.length > 1) return true;

        // ALSO: Check for VISUAL overlap with the single parent.
        const parentNode = nodeMap.get(parentId);
        const myNode = nodeMap.get(nodeId);

        const parentEnd = getEndYear(parentNode);

        // Visual overlap check: parent renders to (parentEnd + 1), so check if that > myStart
        if (parentEnd + 1 > myNode.founding_year) return true; // Visual overlap, break chain

        return false; // No visual overlap, can continue chain
    };

    nodes.forEach(node => {
        if (visited.has(node.id)) return;

        if (isChainStart(node.id)) {
            const chainNodes = [];
            let curr = node.id;

            while (curr) {
                visited.add(curr);
                chainNodes.push(nodeMap.get(curr));

                const s = succs.get(curr) || [];
                // Stop if No Successors
                if (s.length === 0) break;

                // Handling Splits (current node has >1 successor)
                if (s.length > 1) break;

                const nextId = s[0];
                const nextPreds = preds.get(nextId) || [];

                // Handling Merges (next node has >1 predecessors)
                if (nextPreds.length > 1) {
                    // Only continue if 'curr' is the Primary Predecessor
                    if (!isPrimaryContinuation(curr, nextId)) break;

                    // AND if it is the ONLY primary predecessor
                    const primaryPreds = getPrimaryPredecessors(nextId);
                    if (primaryPreds.length !== 1) break;

                    // Also verify we are that predecessor (implicit by length==1 check above + we are primary)
                }

                // Continue
                // CRITICAL: Check for VISUAL overlap (Dirty Data Protection)
                const currNode = nodeMap.get(curr);
                const nextNode = nodeMap.get(nextId);

                const currEnd = getEndYear(currNode);

                if (currEnd + 1 > nextNode.founding_year) {
                    // Visual overlap detected - break chain
                    break;
                }

                curr = nextId;
            }

            chains.push({
                id: chainNodes[0].id,
                nodes: chainNodes,
                startTime: chainNodes[0].founding_year,
                endTime: getEndYear(chainNodes[chainNodes.length - 1]),
                yIndex: 0 // to be assigned
            });
        }
    });

    // Catch-up: If any nodes remain unvisited
    nodes.forEach(node => {
        if (!visited.has(node.id)) {
            visited.add(node.id);
            chains.push({
                id: node.id,
                nodes: [node],
                startTime: node.founding_year,
                endTime: getEndYear(node),
                yIndex: 0
            });
        }
    });

    return chains;
}

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
