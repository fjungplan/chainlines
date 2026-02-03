/**
 * Vertical segment generation utilities for the layout engine
 * Handles the creation of visual vertical connections between parent and child chains
 */

/**
 * Generate vertical segments for visualization based on parent-child relationships
 * 
 * @param {Array} chains - Array of chain objects with id, yIndex, and startTime
 * @param {Map} chainParents - Map of child chain ID to array of parent chain objects
 * @returns {Array} Array of vertical segment objects {y1, y2, time, childId, parentId}
 */
export function generateVerticalSegments(chains, chainParents) {
    const verticalSegments = [];

    chains.forEach(chain => {
        // Incoming (Parents)
        const parents = chainParents.get(chain.id) || [];
        parents.forEach(p => {
            // Only create a segment if they are NOT adjacent (more than 1 lane apart)
            // distance > 1 means there is at least one lane between them
            if (Math.abs(p.yIndex - chain.yIndex) > 1) {
                verticalSegments.push({
                    y1: Math.min(p.yIndex, chain.yIndex),
                    y2: Math.max(p.yIndex, chain.yIndex),
                    time: chain.startTime,
                    childId: chain.id,
                    parentId: p.id
                });
            }
        });
    });

    return verticalSegments;
}
