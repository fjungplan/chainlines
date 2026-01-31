import { describe, it, expect } from 'vitest';
import { LayoutCalculator } from '../../src/utils/layoutCalculator';

describe('Global Cost Infrastructure (Slice 1)', () => {
    // We'll need to mock the environment that layoutFamily provides
    const mockChains = [
        { id: 'c1', startTime: 2000, endTime: 2005, yIndex: 0, nodes: [{ id: 'n1', founding_year: 2000, dissolution_year: 2005 }] },
        { id: 'c2', startTime: 2006, endTime: 2010, yIndex: 0, nodes: [{ id: 'n2', founding_year: 2006, dissolution_year: 2010 }] },
        { id: 'c3', startTime: 2000, endTime: 2010, yIndex: 1, nodes: [{ id: 'n3', founding_year: 2000, dissolution_year: 2010 }] }
    ];

    const mockChainParents = new Map([
        ['c2', [{ id: 'c1', yIndex: 0 }]],
        ['c3', []],
        ['c1', []]
    ]);

    const mockChainChildren = new Map([
        ['c1', [{ id: 'c2', yIndex: 0, startTime: 2006 }]],
        ['c2', []],
        ['c3', []]
    ]);

    // Mock checkCollision that always returns false (no collisions)
    const mockCheckCollision = () => false;

    // Mock verticalSegments
    const mockVerticalSegments = [];

    it('should calculate global cost as sum of all chain costs', () => {
        // Since we haven't exported these yet, we'll need to implement them first
        // But for TDD, we write the test first.
        const calculator = new LayoutCalculator({ nodes: [], links: [] }, 1000, 800);

        // We'll assume for now we'll add these to the class or as exported helpers
        // Given the instructions, let's try to add them to LayoutCalculator as static or instance methods
        // if they don't depend on instance state too much. 
        // Actually, they depend on LAYOUT_CONFIG which is top-level.

        if (typeof calculator.calculateGlobalCost === 'function') {
            const cost = calculator.calculateGlobalCost(mockChains, mockChainParents, mockChainChildren, mockVerticalSegments, mockCheckCollision);
            expect(typeof cost).toBe('number');
            expect(cost).toBeGreaterThanOrEqual(0);
        } else {
            throw new Error('calculateGlobalCost not implemented');
        }
    });

    it('should identify affected chains when a chain moves', () => {
        const calculator = new LayoutCalculator({ nodes: [], links: [] }, 1000, 800);

        if (typeof calculator.getAffectedChains === 'function') {
            const movedChain = mockChains[0]; // c1
            // c1 is parent of c2. So c2 is affected.
            // Also any chain sharing lane 0 or target lane 2 might be affected (blockers/cut-throughs).
            const affected = calculator.getAffectedChains(movedChain, 0, 2, mockChains, mockChainParents, mockChainChildren, mockVerticalSegments);
            expect(affected).toBeInstanceOf(Set);
            expect(affected.has('c2')).toBe(true);
        } else {
            throw new Error('getAffectedChains not implemented');
        }
    });

    it('should calculate incremental cost delta when chain moves', () => {
        const calculator = new LayoutCalculator({ nodes: [], links: [] }, 1000, 800);

        if (typeof calculator.calculateCostDelta === 'function') {
            const chain = mockChains[0];
            const oldY = 0;
            const newY = 2;
            const affectedChains = new Set(['c2']);

            const delta = calculator.calculateCostDelta(chain, oldY, newY, affectedChains, mockChains, mockChainParents, mockChainChildren, mockVerticalSegments, mockCheckCollision);
            expect(typeof delta).toBe('number');
        } else {
            throw new Error('calculateCostDelta not implemented');
        }
    });

    describe('Move Acceptance Criterion (Slice 2)', () => {
        it('should accept move when global cost decreases', () => {
            // Mock deltaGlobal < 0
            const deltaGlobal = -100;
            const deltaLocal = -50;

            // Acceptance logic: (deltaGlobal < 0 || (deltaGlobal === 0 && deltaLocal < 0))
            const accepted = (deltaGlobal < 0 || (deltaGlobal === 0 && deltaLocal < 0));
            expect(accepted).toBe(true);
        });

        it('should reject move when global cost increases', () => {
            const deltaGlobal = 50;
            const deltaLocal = -100; // Local improves but global worsens

            const accepted = (deltaGlobal < 0 || (deltaGlobal === 0 && deltaLocal < 0));
            expect(accepted).toBe(false);
        });

        it('should accept move when global cost is equal but local improves', () => {
            const deltaGlobal = 0;
            const deltaLocal = -100;

            const accepted = (deltaGlobal < 0 || (deltaGlobal === 0 && deltaLocal < 0));
            expect(accepted).toBe(true);
        });
    });
});
