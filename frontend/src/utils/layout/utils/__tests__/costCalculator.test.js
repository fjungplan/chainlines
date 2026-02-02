import { describe, it, expect } from 'vitest';
import { calculateSingleChainCost } from '../costCalculator';
import LAYOUT_CONFIG from '../../layout_config.json';

describe('costCalculator - Overlap Logic Alignment', () => {
    // Mock collision logic (always false for this test as we want to test overlap penalty explicitly)
    const mockCheckCollision = () => false;
    const verticalSegments = [];
    const chainParents = new Map();
    const chainChildren = new Map();

    it('should apply heavy overlap penalty for gap < 2 (Strangers/Family Universal)', () => {
        // Setup: Chain on Lane 0
        // Target: Chain starting at 1980
        // Neighbor: Chain ending at 1980 (Gap = 0)

        const chain = { id: 'target', startTime: 1980, endTime: 1985 };
        const y = 0;

        // Mock ySlots with a neighbor that ends exactly when we start (Gap 0)
        // This is a "touching" scenario which backend penalizes now.
        const ySlots = new Map();
        ySlots.set(0, [
            { chainId: 'neighbor', start: 1970, end: 1980 }
        ]);

        // Calculate Cost
        const cost = calculateSingleChainCost(
            chain,
            y,
            chainParents,
            chainChildren,
            verticalSegments,
            mockCheckCollision,
            ySlots
        );

        // Expected Penalty: OVERLAP_BASE (500,000) + (Magnitude(2) * FACTOR)
        // At minimum it must be > OVERLAP_BASE
        const MIN_OVERLAP_PENALTY = LAYOUT_CONFIG.WEIGHTS.OVERLAP_BASE;

        expect(cost).toBeGreaterThan(MIN_OVERLAP_PENALTY);
    });

    it('should NOT apply overlap penalty for gap = 2', () => {
        // Setup: Chain on Lane 0
        // Target: Chain starting at 1982
        // Neighbor: Chain ending at 1980 (Gap = 2)

        const chain = { id: 'target', startTime: 1982, endTime: 1985 };
        const y = 0;

        const ySlots = new Map();
        ySlots.set(0, [
            { chainId: 'neighbor', start: 1970, end: 1980 }
        ]);

        const cost = calculateSingleChainCost(
            chain,
            y,
            chainParents,
            chainChildren,
            verticalSegments,
            mockCheckCollision,
            ySlots
        );

        // Should be 0 (or very low spacing cost)
        // Definitely less than the massive overlap penalty
        const MIN_OVERLAP_PENALTY = LAYOUT_CONFIG.WEIGHTS.OVERLAP_BASE;
        expect(cost).toBeLessThan(MIN_OVERLAP_PENALTY);
    });
});
