
import { describe, it, expect } from 'vitest';
import { calculateSingleChainCost } from '../costCalculator';

describe('Temporal Overlap Protection', () => {

    it('should penalize linked chains if they actually overlap in time (gap < 0)', () => {
        // Chain A: 1970-1985
        // Chain B: 1980-1990
        // Overlap of 5 years.

        const chainB = {
            id: 'chain_b',
            startTime: 1980,
            endTime: 1990
        };

        const ySlots = new Map();
        ySlots.set(0, [{
            chainId: 'chain_a',
            start: 1970,
            end: 1985
        }]);

        // Mock Maps - Linked
        const chainParents = new Map();
        chainParents.set('chain_b', [{ id: 'chain_a', yIndex: 0 }]);

        const chainChildren = new Map();
        chainChildren.set('chain_a', [{ id: 'chain_b', yIndex: 0 }]);

        const verticalSegments = [];
        const checkCollision = () => false;

        // Run Calculator
        const cost = calculateSingleChainCost(
            chainB,
            0,
            chainParents,
            chainChildren,
            verticalSegments,
            checkCollision,
            ySlots
        );

        // Should have Massive Penalty because gap < 0 (is -5)
        expect(cost).toBeGreaterThan(500000);
    });

    it('should NOT penalize linked chains if they only touch or have small gap (0 <= gap < 2)', () => {
        const chainB = {
            id: 'chain_b',
            startTime: 1980,
            endTime: 1990
        };

        const ySlots = new Map();
        ySlots.set(0, [{
            chainId: 'chain_a',
            start: 1970,
            end: 1980 // Touching
        }]);

        // Mock Maps - Linked
        const chainParents = new Map();
        chainParents.set('chain_b', [{ id: 'chain_a', yIndex: 0 }]);

        const chainChildren = new Map();
        chainChildren.set('chain_a', [{ id: 'chain_b', yIndex: 0 }]);

        const verticalSegments = [];
        const checkCollision = () => false;

        const cost = calculateSingleChainCost(
            chainB,
            0,
            chainParents,
            chainChildren,
            verticalSegments,
            checkCollision,
            ySlots
        );

        // Should NOT have massive penalty
        expect(cost).toBeLessThan(500000);
    });
});
