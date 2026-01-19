import { LAYOUT_CONFIG } from '../config.js';

/**
 * Cost calculation utilities for the layout engine
 * Determines the penalty score for placing a chain at a specific Y position
 */

/**
 * Calculate the cost of placing a chain at a given Y position
 * 
 * Components:
 * 1. Attraction: Geometric distance to parents/children (Quadratic)
 * 2. Cut-Through: Penalty for passing through occupied lanes (connection overlap)
 * 3. Blocker: Penalty for crossing existing vertical segments
 * 4. Y-Shape: Penalty for tightly squeezing merge/split branches
 * 
 * @param {Object} chain - The chain being placed
 * @param {number} y - The potential Y position (lane index)
 * @param {Map} chainParents - Map of chain ID to parents
 * @param {Map} chainChildren - Map of chain ID to children
 * @param {Array} verticalSegments - Array of vertical segment blockers
 * @param {Function} checkCollision - Collision detection function (y, start, end, excludeId, chain)
 * @returns {number} Total cost (lower is better)
 */
export function calculateSingleChainCost(
    chain,
    y,
    chainParents,
    chainChildren,
    verticalSegments,
    checkCollision
) {
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

    let cutThroughCost = 0;
    const CUT_THROUGH_WEIGHT = LAYOUT_CONFIG.WEIGHTS.CUT_THROUGH;

    parents.forEach(p => {
        const y1 = Math.min(p.yIndex, y);
        const y2 = Math.max(p.yIndex, y);
        if (y2 - y1 > 1) {
            for (let lane = y1 + 1; lane < y2; lane++) {
                // Use chain start/start for cut-through check (instantaneous cut)
                if (checkCollision(lane, chain.startTime, chain.startTime, chain.id, chain)) {
                    cutThroughCost += CUT_THROUGH_WEIGHT;
                }
            }
        }
    });

    const children = chainChildren.get(chain.id) || [];
    children.forEach(c => {
        const y1 = Math.min(y, c.yIndex);
        const y2 = Math.max(y, c.yIndex);
        if (y2 - y1 > 1) {
            for (let lane = y1 + 1; lane < y2; lane++) {
                if (checkCollision(lane, c.startTime, c.startTime, chain.id, chain)) {
                    cutThroughCost += CUT_THROUGH_WEIGHT;
                }
            }
        }
    });

    let blockerCost = 0;
    const BLOCKER_WEIGHT = LAYOUT_CONFIG.WEIGHTS.BLOCKER;
    verticalSegments.forEach(seg => {
        if (seg.childId === chain.id || seg.parentId === chain.id) return;
        if (y > seg.y1 && y < seg.y2) {
            // If the chain's timespan overlaps the blocker segment's time
            // Logic: Segments exist at specific 'time'. If chain exists at that time.
            if (seg.time >= chain.startTime && seg.time <= chain.endTime + 1) {
                blockerCost += BLOCKER_WEIGHT;
            }
        }
    });

    let yShapeCost = 0;
    const Y_SHAPE_WEIGHT = LAYOUT_CONFIG.WEIGHTS.Y_SHAPE;

    // Penalty for merging parents being too close (squeezed Y)
    childrenForAttraction.forEach(c => {
        const spouses = chainParents.get(c.id) || [];
        spouses.forEach(spouse => {
            if (spouse.id === chain.id) return;
            if (Math.abs(spouse.yIndex - y) < 2) {
                yShapeCost += Y_SHAPE_WEIGHT;
            }
        });
    });

    // Penalty for splitting children being too close
    parents.forEach(p => {
        const siblings = chainChildren.get(p.id) || [];
        siblings.forEach(sib => {
            if (sib.id === chain.id) return;
            if (Math.abs(sib.yIndex - y) < 2) {
                yShapeCost += Y_SHAPE_WEIGHT;
            }
        });
    });

    return attractionCost + cutThroughCost + blockerCost + yShapeCost;
}
