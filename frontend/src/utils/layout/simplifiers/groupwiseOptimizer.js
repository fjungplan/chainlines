
import { calculateSingleChainCost, calculateCostDelta, getAffectedChains } from '../utils/costCalculator.js';
import { generateVerticalSegments } from '../utils/verticalSegments.js';
import { LAYOUT_CONFIG } from '../config.js';

/**
 * Groupwise Optimization Module (Slice 8)
 * Handles Hybrid Mode optimization: Rigid Moves, Swaps, and Simulated Annealing.
 */

// ============================================================================
// Public API
// ============================================================================

/**
 * Run groupwise optimization pass.
 * Identifies connected groups and applies optimization strategies.
 */
export function runGroupwiseOptimization(familyChains, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots) {

    // 1. Calculate degrees for sorting
    const chainDegrees = new Map();
    familyChains.forEach(c => {
        let deg = 0;
        const parents = chainParents.get(c.id) || [];
        const children = chainChildren.get(c.id) || [];
        deg += parents.length + children.length; // Simple max degree
        chainDegrees.set(c.id, deg);
    });

    // 2. Sort chains (leaves first) to build groups bottom-up
    const sortedChains = sortChainsByDegree(familyChains, chainDegrees);
    const visited = new Set();
    const groups = [];

    // 3. Build Groups
    for (const chain of sortedChains) {
        if (!visited.has(chain)) {
            const group = buildGroup(chain, chains, chainParents, chainChildren);
            if (group.size > 0) {
                groups.push(group);
                group.forEach(c => visited.add(c));
            }
        }
    }

    // 4. Optimize Each Group
    for (const group of groups) {
        let groupImproved = false;

        // Strategy A: Rigid Group Move
        const maxRigidDelta = LAYOUT_CONFIG.GROUPWISE.MAX_RIGID_DELTA;
        const rigidDeltas = calculateRigidMoveDeltas(group, ySlots, checkCollision, maxRigidDelta);

        let bestRigidDelta = 0;
        let bestRigidImprovement = 0;

        for (const delta of rigidDeltas) {
            const deltaCost = evaluateRigidMove(group, delta, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);
            if (deltaCost < bestRigidImprovement) { // Negative cost is better
                bestRigidImprovement = deltaCost;
                bestRigidDelta = delta;
            }
        }

        if (bestRigidImprovement < 0) {
            applyRigidMove(group, bestRigidDelta, ySlots);
            groupImproved = true;
        }

        // Strategy B: Pairwise Swaps
        if (group.size > 1) {
            const bestSwap = findBestSwap(group, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);
            if (bestSwap && bestSwap.delta < 0) {
                applySwap(bestSwap.chainA, bestSwap.chainB, ySlots);
                groupImproved = true;
            }
        }

        // Strategy C: Simulated Annealing Fallback
        if (!groupImproved && group.size > 1) {
            const saRegion = calculateSearchRegion(group, LAYOUT_CONFIG.GROUPWISE.SEARCH_RADIUS);
            const saOptions = {
                maxIterations: LAYOUT_CONFIG.GROUPWISE.SA_MAX_ITER,
                initialTemp: LAYOUT_CONFIG.GROUPWISE.SA_INITIAL_TEMP,
                coolingRate: 0.95
            };
            simulatedAnnealingReposition(group, saRegion, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots, saOptions);
        }
    }
}

// ============================================================================
// Internal Helpers - Group Building
// ============================================================================

function sortChainsByDegree(chains, chainDegrees) {
    return [...chains].sort((a, b) => {
        const degA = chainDegrees.get(a.id) || 0;
        const degB = chainDegrees.get(b.id) || 0;
        return degA - degB;
    });
}

function buildGroup(startChain, chains, chainParents, chainChildren) {
    const group = new Set();
    const queue = [startChain];
    group.add(startChain);

    while (queue.length > 0) {
        const current = queue.shift();
        const parents = chainParents.get(current.id) || [];
        const children = chainChildren.get(current.id) || [];
        const neighbors = [...parents, ...children];

        for (const neighbor of neighbors) {
            if (!group.has(neighbor)) {
                group.add(neighbor);
                queue.push(neighbor);
            }
        }
    }
    return group;
}

// ============================================================================
// Internal Helpers - Rigid Moves
// ============================================================================

function calculateRigidMoveDeltas(group, ySlots, checkCollision, maxDelta) {
    const chains = Array.from(group);
    const validDeltas = [];
    const minY = Math.min(...chains.map(c => c.yIndex));

    for (let delta = -maxDelta; delta <= maxDelta; delta++) {
        if (delta === 0) continue;
        if (minY + delta < 0) continue;

        let hasCollision = false;
        for (const chain of chains) {
            const newY = chain.yIndex + delta;
            if (checkCollision(newY, chain.startTime, chain.endTime, chain.id, chain)) {
                hasCollision = true;
                break;
            }
        }
        if (!hasCollision) validDeltas.push(delta);
    }
    return validDeltas;
}

function evaluateRigidMove(group, delta, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots) {
    const groupChains = Array.from(group);
    const originalPositions = new Map(groupChains.map(c => [c.id, c.yIndex]));

    // Temporarily apply move
    groupChains.forEach(chain => chain.yIndex += delta);

    // Determine affected chains
    const allAffected = new Set();
    groupChains.forEach(chain => {
        const oldY = originalPositions.get(chain.id);
        const newY = chain.yIndex;
        const affected = getAffectedChains(chain, oldY, newY, chains, chainParents, chainChildren, verticalSegments);
        affected.forEach(id => allAffected.add(id));
        allAffected.add(chain.id);
    });

    // Calculate cost delta
    let costDelta = 0;
    allAffected.forEach(chainId => {
        const chain = chains.find(c => c.id === chainId);
        if (chain) {
            // If chain is in group (and thus moved), its "old" position was stored.
            // If chain is outside group, it didn't move, so oldY = yIndex.
            const oldY = originalPositions.has(chain.id) ? originalPositions.get(chain.id) : chain.yIndex;
            const newY = chain.yIndex;

            const oldCost = calculateSingleChainCost(chain, oldY, chainParents, chainChildren, verticalSegments, checkCollision);
            const newCost = calculateSingleChainCost(chain, newY, chainParents, chainChildren, verticalSegments, checkCollision);
            costDelta += (newCost - oldCost);
        }
    });

    // Revert positions
    groupChains.forEach(chain => chain.yIndex = originalPositions.get(chain.id));

    return costDelta;
}

function applyRigidMove(group, delta, ySlots) {
    const chains = Array.from(group);
    const slotsToMove = [];

    chains.forEach(chain => {
        const oldY = chain.yIndex;
        const slots = ySlots.get(oldY);
        if (slots) {
            const idx = slots.findIndex(s => s.chainId === chain.id);
            if (idx !== -1) {
                const slot = slots.splice(idx, 1)[0];
                slotsToMove.push({ slot, oldY, newY: oldY + delta });
            }
        }
    });

    chains.forEach(chain => chain.yIndex += delta);

    slotsToMove.forEach(({ slot, newY }) => {
        if (!ySlots.has(newY)) ySlots.set(newY, []);
        ySlots.get(newY).push(slot);
    });
}

// ============================================================================
// Internal Helpers - Swaps
// ============================================================================

function generatePairwiseCombinations(group) {
    const chains = Array.from(group);
    const pairs = [];
    for (let i = 0; i < chains.length; i++) {
        for (let j = i + 1; j < chains.length; j++) {
            pairs.push([chains[i], chains[j]]);
        }
    }
    return pairs;
}

function findBestSwap(group, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots) {
    const pairs = generatePairwiseCombinations(group);
    let bestSwap = null;
    let bestDelta = 0;

    for (const [chainA, chainB] of pairs) {
        const delta = evaluateSwap(chainA, chainB, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);
        if (delta < bestDelta) {
            bestDelta = delta;
            bestSwap = { chainA, chainB, delta };
        }
    }
    return bestSwap;
}

function evaluateSwap(chainA, chainB, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots) {
    const originalAY = chainA.yIndex;
    const originalBY = chainB.yIndex;

    // Swap Y
    chainA.yIndex = originalBY;
    chainB.yIndex = originalAY;

    // Swap Slots Temporarily
    // Note: evaluateSwap in original code did complex slot swapping.
    // We need to replicate that logic to ensure checkCollision (used inside cost calc) sees correct state.
    // HOWEVER: verifyTotalCostImprovement / calculateCostDelta logic usually handles the slot management.
    // In `evaluateSwap` from LayoutCalculator, it DID manually swap slots.

    const moveSlot = (yFrom, yTo, cId) => {
        const slots = ySlots.get(yFrom);
        let removed = null;
        if (slots) {
            const idx = slots.findIndex(s => s.chainId === cId);
            if (idx !== -1) removed = slots.splice(idx, 1)[0];
        }
        if (removed) {
            if (!ySlots.has(yTo)) ySlots.set(yTo, []);
            ySlots.get(yTo).push(removed);
        }
        return removed;
    };

    const slotA = moveSlot(originalAY, originalBY, chainA.id);
    const slotB = moveSlot(originalBY, originalAY, chainB.id);

    // Calculate Delta
    const affectedA = getAffectedChains(chainA, originalBY, originalAY, chains, chainParents, chainChildren, verticalSegments);
    const affectedB = getAffectedChains(chainB, originalAY, originalBY, chains, chainParents, chainChildren, verticalSegments);
    const allAffected = new Set([...affectedA, ...affectedB, chainA.id, chainB.id]);

    let delta = 0;
    allAffected.forEach(chainId => {
        const chain = chains.find(c => c.id === chainId);
        if (chain) {
            // Determine "old" Y for delta calc.
            // If chain is A or B, old was original position.
            const oldY = (chain.id === chainA.id) ? originalAY : ((chain.id === chainB.id) ? originalBY : chain.yIndex);
            const newY = chain.yIndex;

            const oldCost = calculateSingleChainCost(chain, oldY, chainParents, chainChildren, verticalSegments, checkCollision);
            const newCost = calculateSingleChainCost(chain, newY, chainParents, chainChildren, verticalSegments, checkCollision);
            delta += (newCost - oldCost);
        }
    });

    // Revert
    chainA.yIndex = originalAY;
    chainB.yIndex = originalBY;

    // Revert slots
    // Move back from new pos to old pos
    if (slotA) moveSlot(originalBY, originalAY, chainA.id);
    if (slotB) moveSlot(originalAY, originalBY, chainB.id);

    return delta;
}

function applySwap(chainA, chainB, ySlots) {
    const tempY = chainA.yIndex;
    const targetY = chainB.yIndex;

    // Swap Indices
    chainA.yIndex = targetY;
    chainB.yIndex = tempY;

    // Swap Slots
    const moveSlot = (yFrom, yTo, cId) => {
        const slots = ySlots.get(yFrom);
        if (slots) {
            const idx = slots.findIndex(s => s.chainId === cId);
            if (idx !== -1) {
                const slot = slots.splice(idx, 1)[0];
                if (!ySlots.has(yTo)) ySlots.set(yTo, []);
                ySlots.get(yTo).push(slot);
            }
        }
    };

    moveSlot(tempY, targetY, chainA.id); // Move A to B's spot
    moveSlot(targetY, tempY, chainB.id); // Move B to A's spot (which is now tempY... wait. B was at targetY)
    // Actually: A was at tempY. B was at targetY.
    // A moves tempY -> targetY.
    // B moves targetY -> tempY.
    // Order matters if they overlap? They shouldn't be in same slot.
}

// ============================================================================
// Internal Helpers - Simulated Annealing
// ============================================================================

function calculateSearchRegion(group, radius) {
    const chains = Array.from(group);
    const minChainY = Math.min(...chains.map(c => c.yIndex));
    const maxChainY = Math.max(...chains.map(c => c.yIndex));
    let minY = minChainY - radius;
    let maxY = maxChainY + radius;
    if (minY < 0) minY = 0;
    return { minY, maxY };
}

function simulatedAnnealingReposition(group, region, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots, options) {
    const { maxIterations, initialTemp, coolingRate } = options;
    const groupChains = Array.from(group);

    // Initial Cost
    let currentCost = 0;
    groupChains.forEach(c => {
        currentCost += calculateSingleChainCost(c, c.yIndex, chainParents, chainChildren, verticalSegments, checkCollision);
    });

    let bestCost = currentCost;
    let bestPositions = new Map(groupChains.map(c => [c.id, c.yIndex]));

    for (let iter = 0; iter < maxIterations; iter++) {
        const temp = initialTemp * Math.pow(coolingRate, iter);
        const randomChain = groupChains[Math.floor(Math.random() * groupChains.length)];
        const oldY = randomChain.yIndex;
        const newY = Math.floor(Math.random() * (region.maxY - region.minY + 1)) + region.minY;

        if (newY === oldY || checkCollision(newY, randomChain.startTime, randomChain.endTime, randomChain.id, randomChain)) continue;

        const affected = getAffectedChains(randomChain, oldY, newY, chains, chainParents, chainChildren, verticalSegments);
        const delta = calculateCostDelta(randomChain, oldY, newY, affected, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);

        // Accept?
        if (delta < 0 || Math.random() < Math.exp(-delta / temp)) {
            // Apply
            const slots = ySlots.get(oldY);
            if (slots) {
                const idx = slots.findIndex(s => s.chainId === randomChain.id);
                if (idx !== -1) {
                    const slot = slots.splice(idx, 1)[0];
                    if (!ySlots.has(newY)) ySlots.set(newY, []);
                    ySlots.get(newY).push(slot);
                }
            }
            randomChain.yIndex = newY;
            currentCost += delta;

            if (currentCost < bestCost) {
                bestCost = currentCost;
                bestPositions = new Map(groupChains.map(c => [c.id, c.yIndex]));
            }
        }
    }

    // Restore Best
    if (currentCost > bestCost) {
        groupChains.forEach(chain => {
            const oldY = chain.yIndex;
            const newY = bestPositions.get(chain.id);
            if (oldY !== newY) {
                // Move slot
                const slots = ySlots.get(oldY);
                if (slots) {
                    const idx = slots.findIndex(s => s.chainId === chain.id);
                    if (idx !== -1) {
                        const slot = slots.splice(idx, 1)[0];
                        if (!ySlots.has(newY)) ySlots.set(newY, []);
                        ySlots.get(newY).push(slot);
                    }
                }
                chain.yIndex = newY;
            }
        });
    }
}
