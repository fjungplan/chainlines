import { describe, it, expect, beforeEach } from 'vitest';
import { LayoutCalculator } from '../../src/utils/layoutCalculator';

describe('LayoutCalculator - Slice 6: Simulated Annealing Fallback', () => {
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

        const chainA = { id: 'A', startTime: 1900, endTime: 1910, yIndex: 5 };
        const chainB = { id: 'B', startTime: 1910, endTime: 1920, yIndex: 7 };
        const chainC = { id: 'C', startTime: 1920, endTime: 1930, yIndex: 9 };

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
            [5, [{ start: 1900, end: 1910, chainId: 'A' }]],
            [7, [{ start: 1910, end: 1920, chainId: 'B' }]],
            [9, [{ start: 1920, end: 1930, chainId: 'C' }]]
        ]);

        mockVerticalSegments = [];
        checkCollision = () => false;
    });

    it('should define bounded search region for group', () => {
        // Current group at [5, 7, 9], search ±10 lanes
        const radius = 10;
        const region = layoutCalc._calculateSearchRegion(mockGroup, radius);

        expect(region).toHaveProperty('minY');
        expect(region).toHaveProperty('maxY');

        // Region should be at least as wide as radius
        expect(region.maxY - region.minY).toBeGreaterThanOrEqual(radius);

        // Should be clamped to non-negative
        expect(region.minY).toBeGreaterThanOrEqual(0);
    });

    it('should clamp search region to prevent negative yIndex', () => {
        // Group close to zero
        const chainLow = { id: 'Low', startTime: 2000, endTime: 2010, yIndex: 2 };
        const groupLow = new Set([chainLow]);

        const radius = 10;
        const region = layoutCalc._calculateSearchRegion(groupLow, radius);

        // Min should be clamped to 0
        expect(region.minY).toBe(0);
    });

    it('should accept worse solutions with decreasing probability', () => {
        // This is a probabilistic test - we can't test exact behavior
        // but we can verify the method exists and returns boolean
        const deltaCost = 100; // Positive (worse)
        const highTemp = 100;
        const lowTemp = 1;

        // High temperature should be more likely to accept
        let highTempAccepts = 0;
        let lowTempAccepts = 0;
        const trials = 100;

        for (let i = 0; i < trials; i++) {
            if (layoutCalc._acceptMove(deltaCost, highTemp)) highTempAccepts++;
            if (layoutCalc._acceptMove(deltaCost, lowTemp)) lowTempAccepts++;
        }

        // High temp should accept more often than low temp (statistically)
        // Using a loose bound to avoid flakiness
        expect(highTempAccepts).toBeGreaterThan(lowTempAccepts);
    });

    it('should always accept improving solutions', () => {
        const deltaCost = -100; // Negative (better)
        const temperature = 50;

        // Should always accept improvements regardless of temperature
        for (let i = 0; i < 10; i++) {
            expect(layoutCalc._acceptMove(deltaCost, temperature)).toBe(true);
        }
    });

    it('should run simulated annealing and return result', () => {
        const region = { minY: 0, maxY: 20 };
        const options = {
            maxIterations: 20,
            initialTemp: 100,
            coolingRate: 0.95
        };

        const result = layoutCalc._simulatedAnnealingReposition(
            mockGroup,
            region,
            mockChains,
            mockParents,
            mockChildren,
            mockVerticalSegments,
            checkCollision,
            mockYSlots,
            options
        );

        expect(result).toHaveProperty('improved');
        expect(result).toHaveProperty('finalCost');
        expect(typeof result.improved).toBe('boolean');
        expect(typeof result.finalCost).toBe('number');
    });

    it('should converge to equal or better global cost', () => {
        // Calculate initial cost
        let initialCost = 0;
        mockGroup.forEach(chain => {
            const cost = layoutCalc._calculateSingleChainCost(
                chain,
                chain.yIndex,
                mockParents,
                mockChildren,
                mockVerticalSegments,
                checkCollision
            );
            initialCost += cost;
        });

        const region = { minY: 0, maxY: 20 };
        const options = {
            maxIterations: 50,
            initialTemp: 100,
            coolingRate: 0.9
        };

        const result = layoutCalc._simulatedAnnealingReposition(
            mockGroup,
            region,
            mockChains,
            mockParents,
            mockChildren,
            mockVerticalSegments,
            checkCollision,
            mockYSlots,
            options
        );

        // Final cost should be <= initial cost (or very close due to randomness)
        // Using a small tolerance for stochastic nature
        expect(result.finalCost).toBeLessThanOrEqual(initialCost + 1);
    });

    it('should update ySlots after successful annealing', () => {
        const region = { minY: 0, maxY: 20 };
        const options = {
            maxIterations: 30,
            initialTemp: 100,
            coolingRate: 0.9
        };

        const originalPositions = mockChains.map(c => c.yIndex);

        layoutCalc._simulatedAnnealingReposition(
            mockGroup,
            region,
            mockChains,
            mockParents,
            mockChildren,
            mockVerticalSegments,
            checkCollision,
            mockYSlots,
            options
        );

        // ySlots should be consistent with current positions
        mockChains.forEach(chain => {
            const slots = mockYSlots.get(chain.yIndex);
            expect(slots).toBeDefined();
            expect(slots.some(s => s.chainId === chain.id)).toBe(true);
        });
    });
});
