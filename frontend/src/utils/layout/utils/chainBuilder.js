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

    // Link Map for fast lookup of {source, target} -> {year, type}
    const linkMap = new Map();
    links.forEach(l => {
        linkMap.set(`${l.source}-${l.target}`, {
            year: l.year || l.event_year,
            type: l.event_type || l.type
        });
    });

    // Helper: Is this a "Primary Continuation" based on time? (Hand-off)
    // A continuation is primary if:
    // 1. It is a LEGAL_TRANSFER
    // OR 2. The link alignment and node boundaries suggest a direct hand-off.
    const isPrimaryContinuation = (parentId, childId) => {
        const link = linkMap.get(`${parentId}-${childId}`);
        const childNode = nodeMap.get(childId);
        const parentNode = nodeMap.get(parentId);

        if (!link || !childNode || !parentNode) return false;

        // Rule: LEGAL_TRANSFER is always a continuation candidate
        if (link.type === "LEGAL_TRANSFER") return true;

        const linkYear = link.year;
        const childStart = childNode.founding_year;
        const parentEnd = getEndYear(parentNode);

        // If link year is available, it MUST match the child birth
        if (linkYear !== undefined) {
            if (Math.abs(linkYear - childStart) > 1) return false;
            // Furthermore, for it to be a "hand-off" (vs a mid-life split),
            // it should be near the parent's death.
            if (Math.abs(linkYear - parentEnd) > 1 && linkYear < parentEnd) return false;
            return true;
        }

        // Fallback: No link year. Compare node boundaries directly.
        // A direct hand-off is when child starts near parent end.
        return Math.abs(childStart - parentEnd) <= 1;
    };

    const currentYear = new Date().getFullYear();

    const getEndYear = (node) => {
        if (!node) return currentYear;
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

    /**
     * Identify the unique 'chosen' successor that continues this node's chain.
     */
    const getChosenSuccessor = (nodeId) => {
        const sIds = succs.get(nodeId) || [];
        if (sIds.length === 0) return null;

        // Filter for candidates that are primary continuations
        const candidates = sIds.filter(sId => isPrimaryContinuation(nodeId, sId));

        if (candidates.length === 0) return null;
        if (candidates.length === 1) return candidates[0];

        // Resolve Ambiguity: Check for unique LEGAL_TRANSFER among candidates
        const legalCandidates = candidates.filter(sId => {
            const link = linkMap.get(`${nodeId}-${sId}`);
            return link && link.type === "LEGAL_TRANSFER";
        });

        if (legalCandidates.length === 1) return legalCandidates[0];
        return null;
    };

    /**
     * Identify the unique 'chosen' predecessor that this node continues the chain from.
     */
    const getChosenPredecessor = (nodeId) => {
        const pIds = preds.get(nodeId) || [];
        if (pIds.length === 0) return null;

        // Filter for candidates that are primary continuations
        const candidates = pIds.filter(pId => isPrimaryContinuation(pId, nodeId));

        if (candidates.length === 0) return null;
        if (candidates.length === 1) return candidates[0];

        // Resolve Ambiguity: Check for unique LEGAL_TRANSFER among candidates
        const legalCandidates = candidates.filter(pId => {
            const link = linkMap.get(`${pId}-${nodeId}`);
            return link && link.type === "LEGAL_TRANSFER";
        });

        if (legalCandidates.length === 1) return legalCandidates[0];
        return null;
    };

    // 1. Identification of "Chain Starter" nodes
    const isChainStart = (nodeId) => {
        // A node starts a chain if it has no chosen predecessor,
        // OR if its chosen predecessor has a different chosen successor (split conflict).
        const pId = getChosenPredecessor(nodeId);
        if (!pId) return true;

        // Check if parent chooses US as the primary continuation
        if (getChosenSuccessor(pId) !== nodeId) return true;

        // ALSO: Check for VISUAL overlap with the chosen parent.
        const parentNode = nodeMap.get(pId);
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

                // Find the unique logical continuation
                const nextId = getChosenSuccessor(curr);
                if (!nextId) break;

                // Symmetry check: handle merges
                // The next node MUST choose MUST choose US as its primary predecessor
                if (getChosenPredecessor(nextId) !== curr) break;

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
