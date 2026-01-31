import { describe, it, expect, beforeEach } from 'vitest';
import { LayoutCalculator } from '../../src/utils/layoutCalculator';

describe('LayoutCalculator - Slice 4: Pairwise Swap Operations', () => {
    let layoutCalc;
    let mockChains;
    let mockParents;
    let mockChildren;
    let mockYSlots;
    let mockVerticalSegments;

    beforeEach(() => {
        layoutCalc = new LayoutCalculator({ nodes: [], links: [] }, 1000, 800);

        const chainA = { id: 'A', startTime: 1900, endTime: 1910, yIndex: 0 };
        const chainB = { id: 'B', startTime: 1910, endTime: 1920, yIndex: 2 };
        const chainC = { id: 'C', startTime: 1920, endTime: 1930, yIndex: 4 };

        mockChains = [chainA, chainB, chainC];

        mockParents = new Map([
            ['A', []],
            ['B', [chainA]],
            ['C', [chainB]]
        ]);

        mockChildren = new Map([
            ['A', [chainB]],
            ['B', [chainC]],
            ['C', []]
        ]);

        mockYSlots = new Map([
            [0, [{ start: 1900, end: 1910, chainId: 'A' }]],
            [2, [{ start: 1910, end: 1920, chainId: 'B' }]],
            [4, [{ start: 1920, end: 1930, chainId: 'C' }]]
        ]);

        mockVerticalSegments = [];
    });

    it('should generate all pairwise combinations for a group', () => {
        const group = new Set(mockChains);
        const pairs = layoutCalc._generatePairwiseCombinations(group);

        expect(pairs).toHaveLength(3); // C(3,2) = 3

        // Verify we have all unique pairs
        const pairIds = pairs.map(p => `${p[0].id}-${p[1].id}`).sort();
        expect(pairIds).toContain('A-B');
        expect(pairIds).toContain('A-C');
        expect(pairIds).toContain('B-C');
    });

    it('should handle single-chain group (no pairs)', () => {
        const group = new Set([mockChains[0]]);
        const pairs = layoutCalc._generatePairwiseCombinations(group);
        expect(pairs).toHaveLength(0);
    });

    it('should evaluate swap and calculate global cost delta', () => {
        // Swap A (lane 0) with B (lane 2)
        const checkCollision = () => false; // Mock: no collisions

        const delta = layoutCalc._evaluateSwap(
            mockChains[0],
            mockChains[1],
            mockChains,
            mockParents,
            mockChildren,
            mockVerticalSegments,
            checkCollision,
            mockYSlots
        );

        // Delta should be a number (could be positive, negative, or zero)
        expect(typeof delta).toBe('number');
    });

    it('should find best swap that maximizes global cost reduction', () => {
        const group = new Set(mockChains);
        const checkCollision = () => false;

        const bestSwap = layoutCalc._findBestSwap(
            group,
            mockChains,
            mockParents,
            mockChildren,
            mockVerticalSegments,
            checkCollision,
            mockYSlots
        );

        // bestSwap should be null (no improvement) or an object with chainA, chainB, delta
        if (bestSwap !== null) {
            expect(bestSwap).toHaveProperty('chainA');
            expect(bestSwap).toHaveProperty('chainB');
            expect(bestSwap).toHaveProperty('delta');
            expect(bestSwap.delta).toBeLessThan(0); // Only return if improvement
        }
    });

    it('should return null if no swap improves global cost', () => {
        // Create a scenario where swaps don't help
        const isolatedChain = { id: 'Iso', startTime: 2000, endTime: 2010, yIndex: 10 };
        const group = new Set([isolatedChain]);
        const checkCollision = () => false;

        const bestSwap = layoutCalc._findBestSwap(
            group,
            [isolatedChain],
            new Map([['Iso', []]]),
            new Map([['Iso', []]]),
            [],
            checkCollision,
            new Map([[10, [{ start: 2000, end: 2010, chainId: 'Iso' }]]])
        );

        expect(bestSwap).toBeNull();
    });

    it('should apply swap by exchanging yIndex values', () => {
        const chainA = mockChains[0];
        const chainB = mockChains[1];
        const originalAY = chainA.yIndex;
        const originalBY = chainB.yIndex;

        layoutCalc._applySwap(chainA, chainB, mockYSlots);

        // yIndex values should be swapped
        expect(chainA.yIndex).toBe(originalBY);
        expect(chainB.yIndex).toBe(originalAY);

        // ySlots should be updated
        expect(mockYSlots.get(originalBY).some(s => s.chainId === 'A')).toBe(true);
        expect(mockYSlots.get(originalAY).some(s => s.chainId === 'B')).toBe(true);
    });
});
