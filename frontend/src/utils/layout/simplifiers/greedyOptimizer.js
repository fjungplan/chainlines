
import { calculateSingleChainCost, calculateCostDelta, getAffectedChains } from '../utils/costCalculator.js';
import LAYOUT_CONFIG from '../layout_config.json';

/**
 * Greedy Optimization Module
 * Iteratively improves layout by moving chains to locally optimal positions.
 */

/**
 * Runs a single pass of greedy optimization on the provided family.
 * 
 * @param {Array<Object>} family - The chains in the current connected component
 * @param {Array<Object>} chains - All chains (context)
 * @param {Map} chainParents - Map of chain ID to parents
 * @param {Map} chainChildren - Map of chain ID to children
 * @param {Array} verticalSegments - Array of vertical segment blockers
 * @param {Function} checkCollision - Collision detection function
 * @param {Map} ySlots - Map of Y-index to occupied slots
 * @param {string} strategy - Sorting strategy ('PARENTS', 'CHILDREN', 'HUBS')
 */
export function runGreedyPass(family, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots, strategy) {
    const sortedChains = Array.from(family);

    // 1. Sort
    if (strategy === 'PARENTS') {
        sortedChains.sort((a, b) => a.startTime - b.startTime);
    } else if (strategy === 'CHILDREN') {
        sortedChains.sort((a, b) => b.startTime - a.startTime);
    } else if (strategy === 'HUBS') {
        const getDegree = (c) => (chainParents.get(c.id)?.length || 0) + (chainChildren.get(c.id)?.length || 0);
        sortedChains.sort((a, b) => getDegree(b) - getDegree(a));
    }

    // 2. Optimize each chain (Greedy Layout Move)
    for (const chain of sortedChains) {
        const currentY = chain.yIndex;

        // A. Identify Candidates
        // ----------------------
        let candidates = new Set();
        // Always include current position
        candidates.add(currentY);

        // 1. Local Neighborhood
        for (let dy = -LAYOUT_CONFIG.SEARCH_RADIUS; dy <= LAYOUT_CONFIG.SEARCH_RADIUS; dy++) {
            candidates.add(currentY + dy);
        }

        // 2. Parent Vicinity
        const parents = chainParents.get(chain.id) || [];
        for (const p of parents) {
            const parentChain = chains.find(c => c.id === p.id);
            if (parentChain) {
                const py = parentChain.yIndex;
                for (let dy = -LAYOUT_CONFIG.TARGET_RADIUS; dy <= LAYOUT_CONFIG.TARGET_RADIUS; dy++) {
                    candidates.add(py + dy);
                }
            }
        }

        // 3. Child Vicinity
        const children = chainChildren.get(chain.id) || [];
        for (const c of children) {
            const childChain = chains.find(ch => ch.id === c.id);
            if (childChain) {
                const cy = childChain.yIndex;
                for (let dy = -LAYOUT_CONFIG.TARGET_RADIUS; dy <= LAYOUT_CONFIG.TARGET_RADIUS; dy++) {
                    candidates.add(cy + dy);
                }
            }
        }

        // B. Evaluate Candidates
        // ----------------------
        let bestY = currentY;

        // Calculate current cost (baseline)
        const currentCost = calculateSingleChainCost(chain, currentY, chainParents, chainChildren, verticalSegments, checkCollision);
        let minCost = currentCost;

        const candidateArray = Array.from(candidates).sort((a, b) => a - b);

        for (const y of candidateArray) {
            if (y === currentY) continue;

            // 1. Collision Check
            if (checkCollision(y, chain.startTime, chain.endTime, chain.id, chain)) continue;

            // 2. Cost Calculation
            const cost = calculateSingleChainCost(chain, y, chainParents, chainChildren, verticalSegments, checkCollision);

            // 3. Selection
            // STRICTLY BETTER acceptance for main loop
            if (cost < minCost) {
                minCost = cost;
                bestY = y;
            }
        }

        // C. Apply Move (Global Acceptance Check)
        // ---------------------------------------
        // We only move if it passes the Net Global Cost improvement check (Slice 2 logic)
        if (bestY !== currentY) {
            const affectedChains = getAffectedChains(chain, currentY, bestY, chains, chainParents, chainChildren, verticalSegments);

            const delta = calculateCostDelta(chain, currentY, bestY, affectedChains, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);

            // If delta is negative, implementation improves cost
            if (delta < 0) {
                // Apply Move
                const oldSlots = ySlots.get(currentY);
                if (oldSlots) {
                    const idx = oldSlots.findIndex(s => s.chainId === chain.id);
                    if (idx !== -1) oldSlots.splice(idx, 1);
                }

                chain.yIndex = bestY;

                if (!ySlots.has(bestY)) ySlots.set(bestY, []);
                ySlots.get(bestY).push({
                    start: chain.startTime,
                    end: chain.endTime,
                    chainId: chain.id
                });
            }
        }
    }
}
