/**
 * Collision detection utilities for the layout engine
 * Handles family-aware collision checking with temporal gap requirements
 */

/**
 * Check if placing a chain at a given Y position would collide with existing chains
 * 
 * Family-aware collision rules:
 * - Family members (parents/children) can overlap temporally
 * - Strangers require a 1-year gap between chains
 * 
 * @param {number} y - The Y position (lane) to check
 * @param {number} start - Start year of the chain being placed
 * @param {number} end - End year of the chain being placed
 * @param {string|null} excludeChainId - Chain ID to exclude from collision check (usually the moving chain itself)
 * @param {Object} movingChain - The chain object being moved/placed
 * @param {Map} ySlots - Map of Y positions to arrays of occupied slots {start, end, chainId}
 * @param {Object} family - Family object containing chains array
 * @param {Map} chainParents - Map of chain ID to array of parent chains
 * @param {Map} chainChildren - Map of chain ID to array of child chains
 * @returns {boolean} True if there is a collision, false otherwise
 */
export function checkCollision(
    y,
    start,
    end,
    excludeChainId,
    movingChain,
    ySlots,
    family,
    chainParents,
    chainChildren
) {
    if (!ySlots.has(y)) return false;
    const slots = ySlots.get(y);

    const collision = slots.some(s => {
        if (s.chainId === excludeChainId) return false;

        // Check if this slot's chain is family (parent or child)
        const slotChain = family.chains.find(c => c.id === s.chainId);
        if (!slotChain) return false;

        const parents = chainParents.get(movingChain.id) || [];
        const children = chainChildren.get(movingChain.id) || [];
        const isFamily = parents.some(p => p.id === s.chainId) ||
            children.some(c => c.id === s.chainId);

        if (isFamily) {
            // Family: allow overlap, use standard collision (touching is OK)
            return !(s.end < start || s.start > end);
        } else {
            // Strangers: enforce 1-year gap
            // Node renders to end+1, so we need: s.end+1 < start OR s.start > end+1
            // Collision if NOT (gap >= 1)
            return !(s.end + 1 < start || s.start > end + 1);
        }
    });
    return collision;
}
