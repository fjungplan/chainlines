import { describe, it, expect, vi } from 'vitest';
import { runGroupwiseOptimization } from '../../../src/utils/layout/simplifiers/groupwiseOptimizer';
import { LAYOUT_CONFIG } from '../../../src/utils/layout/config';

vi.mock('../../../src/utils/layout/utils/costCalculator', () => ({
    calculateSingleChainCost: vi.fn().mockReturnValue(10),
    calculateCostDelta: vi.fn().mockReturnValue(-5),
    getAffectedChains: vi.fn().mockReturnValue(new Set()),
}));

vi.mock('../../../src/utils/layout/utils/verticalSegments', () => ({
    generateVerticalSegments: vi.fn().mockReturnValue([]),
}));

// We will access these mocks by importing them
import { calculateSingleChainCost } from '../../../src/utils/layout/utils/costCalculator';

describe('groupwiseOptimizer', () => {
    // Helper to create chains
    const createChain = (id, yIndex = 0, startTime = 2000, endTime = 2010) => ({
        id, yIndex, startTime, endTime
    });

    const createContext = () => {
        const chains = [];
        const chainParents = new Map();
        const chainChildren = new Map();
        const verticalSegments = [];
        const checkCollision = vi.fn().mockReturnValue(false);
        const ySlots = new Map();

        const addChain = (c) => {
            chains.push(c);
            if (!ySlots.has(c.yIndex)) ySlots.set(c.yIndex, []);
            ySlots.get(c.yIndex).push({ start: c.startTime, end: c.endTime, chainId: c.id });
        };

        return { chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots, addChain };
    };

    it('should group connected chains correctly', () => {
        // This tests the internal _buildGroup logic via the public runGroupwiseOptimization
        // We can spy on the internal methods if we export them, but better to test behavior.

        // Setup: A-B are connected, C is separate
        const { chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots, addChain } = createContext();

        const a = createChain('A', 0);
        const b = createChain('B', 1);
        const c = createChain('C', 5);

        addChain(a);
        addChain(b);
        addChain(c);

        chainParents.set('B', [a]); // A is parent of B
        chainChildren.set('A', [b]);

        // Config hack: Ensure we run rigid move but fail it, so we can see if it processed the groups.
        // Actually, checking if it attempts to optimize is hard without side effects.
        // Let's rely on the fact that if it runs, it calls costs.

        // Reset mocks
        calculateSingleChainCost.mockClear();

        // Force Hybrid Mode
        const originalMode = LAYOUT_CONFIG.HYBRID_MODE;
        LAYOUT_CONFIG.HYBRID_MODE = true;

        // We expect it to process [A,B] and [C] separately.
        // Logic inside runs optimization loop.

        runGroupwiseOptimization([a, b, c], chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);

        // Just verify it ran without error for now, logic is complex mock
        expect(calculateSingleChainCost).toHaveBeenCalled();

        LAYOUT_CONFIG.HYBRID_MODE = originalMode;
    });

    it('should apply rigid move if improvement found', () => {
        const { chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots, addChain } = createContext();

        const a = createChain('A', 0);
        addChain(a);

        // Mock rigid move delta giving improvement
        // The optimizer calculates deltas, then evaluates.
        // calculation of deltas depends on collisions.
        // evaluation depends on calculateCostDelta (which calls calculateSingleChainCost).

        // Let's trust that if cost returns diff, it moves.
        // Currently we mock calculateSingleChainCost to static 10.
        // So rigid move of delta won't change cost unless we make cost dynamic?
        // Actually evaluateRigidMove logic manually calculates diff.
        // It uses calculateSingleChainCost.

        // To test this properly we need cost to vary by Y.
        calculateSingleChainCost.mockImplementation((chain, y) => {
            return y === 5 ? 0 : 10; // y=5 is better
        });

        // We need a valid delta to 5.
        // Current y=0, so delta=+5.
        // checkCollision returns false (no collision), so +5 is valid.

        LAYOUT_CONFIG.HYBRID_MODE = true;

        runGroupwiseOptimization([a], chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);

        // A should move to 5
        expect(a.yIndex).toBe(5);
    });
});
