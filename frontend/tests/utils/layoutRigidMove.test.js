import { describe, it, expect, beforeEach } from 'vitest';
import { LayoutCalculator } from '../../src/utils/layoutCalculator';

describe('LayoutCalculator - Slice 5: Rigid Group Move', () => {
    let layoutCalc;
    let mockGroup;
    let mockChains;
    let mockParents;
    let mockChildren;
    let mockYSlots;
    let mockVerticalSegments;
    let checkCollision;

    beforeEach(() => {
        layoutCalc = new LayoutCalculator({ nodes: [], links: [] }, 1000, 800);

        const chainA = { id: 'A', startTime: 1900, endTime: 1910, yIndex: 3 };
        const chainB = { id: 'B', startTime: 1910, endTime: 1920, yIndex: 5 };
        const chainC = { id: 'C', startTime: 1920, endTime: 1930, yIndex: 7 };

        mockChains = [chainA, chainB, chainC];
        mockGroup = new Set(mockChains);

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
            [3, [{ start: 1900, end: 1910, chainId: 'A' }]],
            [5, [{ start: 1910, end: 1920, chainId: 'B' }]],
            [7, [{ start: 1920, end: 1930, chainId: 'C' }]]
        ]);

        mockVerticalSegments = [];

        // Mock collision checker - no collisions by default
        checkCollision = () => false;
    });

    it('should calculate valid deltas for rigid move', () => {
        // Group at [3, 5, 7], can move to [1, 3, 5] (delta -2)
        const maxDelta = 5;
        const deltas = layoutCalc._calculateRigidMoveDeltas(mockGroup, mockYSlots, checkCollision, maxDelta);

        expect(Array.isArray(deltas)).toBe(true);
        expect(deltas.length).toBeGreaterThan(0);

        // Should include negative deltas (moving up)
        expect(deltas.some(d => d < 0)).toBe(true);

        // Should not exceed maxDelta
        expect(deltas.every(d => Math.abs(d) <= maxDelta)).toBe(true);
    });

    it('should reject rigid move if any chain would collide', () => {
        // Create collision checker that blocks delta -1
        const blockingCollision = (y, startTime, endTime, chainId) => {
            // Block lane 2 (which would be A's new position with delta -1)
            if (y === 2) return true;
            return false;
        };

        const maxDelta = 5;
        const deltas = layoutCalc._calculateRigidMoveDeltas(mockGroup, mockYSlots, blockingCollision, maxDelta);

        // Delta -1 should not be in the list
        expect(deltas.includes(-1)).toBe(false);
    });

    it('should evaluate rigid move and calculate global cost delta', () => {
        const delta = -2; // Move group up by 2 lanes

        const costDelta = layoutCalc._evaluateRigidMove(
            mockGroup,
            delta,
            mockChains,
            mockParents,
            mockChildren,
            mockVerticalSegments,
            checkCollision,
            mockYSlots
        );

        // Should return a number
        expect(typeof costDelta).toBe('number');
    });

    it('should apply rigid move by shifting all chains by same delta', () => {
        const delta = -2;
        const originalPositions = mockChains.map(c => c.yIndex);

        layoutCalc._applyRigidMove(mockGroup, delta, mockYSlots);

        // All chains should be shifted by delta
        mockChains.forEach((chain, idx) => {
            expect(chain.yIndex).toBe(originalPositions[idx] + delta);
        });

        // ySlots should be updated
        expect(mockYSlots.get(1).some(s => s.chainId === 'A')).toBe(true);
        expect(mockYSlots.get(3).some(s => s.chainId === 'B')).toBe(true);
        expect(mockYSlots.get(5).some(s => s.chainId === 'C')).toBe(true);

        // Old slots should be cleared
        expect(mockYSlots.get(7)?.some(s => s.chainId === 'C')).toBe(false);
    });

    it('should preserve relative spacing during rigid move', () => {
        const delta = 3;
        const originalSpacing = [
            mockChains[1].yIndex - mockChains[0].yIndex,
            mockChains[2].yIndex - mockChains[1].yIndex
        ];

        layoutCalc._applyRigidMove(mockGroup, delta, mockYSlots);

        const newSpacing = [
            mockChains[1].yIndex - mockChains[0].yIndex,
            mockChains[2].yIndex - mockChains[1].yIndex
        ];

        // Spacing should be preserved
        expect(newSpacing[0]).toBe(originalSpacing[0]);
        expect(newSpacing[1]).toBe(originalSpacing[1]);
    });

    it('should handle edge case of delta 0 (no move)', () => {
        const delta = 0;
        const originalPositions = mockChains.map(c => c.yIndex);

        layoutCalc._applyRigidMove(mockGroup, delta, mockYSlots);

        // Positions should remain unchanged
        mockChains.forEach((chain, idx) => {
            expect(chain.yIndex).toBe(originalPositions[idx]);
        });
    });

    it('should not allow moves that would result in negative yIndex', () => {
        const maxDelta = 10;
        const deltas = layoutCalc._calculateRigidMoveDeltas(mockGroup, mockYSlots, checkCollision, maxDelta);

        // Min yIndex in group is 3, so delta should not go below -3
        expect(deltas.every(d => d >= -3)).toBe(true);
    });
});
