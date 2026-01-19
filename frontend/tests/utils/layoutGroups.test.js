import { describe, it, expect, beforeEach } from 'vitest';
import { LayoutCalculator } from '../../src/utils/layoutCalculator';

describe('LayoutCalculator - Slice 3: Bottom-Up Group Builder', () => {
    let layoutCalc;
    let mockChains;
    let mockParents;
    let mockChildren;

    beforeEach(() => {
        layoutCalc = new LayoutCalculator({ nodes: [], links: [] }, 1000, 800);

        const chainA = { id: 'A', startTime: 1900, endTime: 1910, yIndex: 0 };
        const chainB = { id: 'B', startTime: 1910, endTime: 1920, yIndex: 1 };
        const chainC = { id: 'C', startTime: 1920, endTime: 1930, yIndex: 2 };

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
    });

    it('should sort chains by degree ASC (Leaves/Roots first, Hubs last)', () => {
        const chainDegrees = new Map([
            ['A', 1],
            ['B', 2],
            ['C', 1]
        ]);

        // We expect the method to return a NEW array sorted by degree
        const sorted = layoutCalc._sortChainsByDegree([...mockChains], chainDegrees);

        expect(sorted).toHaveLength(3);
        // A and C have degree 1, B has degree 2.
        // So B should be last.
        expect(sorted[2].id).toBe('B');
        expect(sorted[0].id).toMatch(/^[AC]$/);
        expect(sorted[1].id).toMatch(/^[AC]$/);
    });

    it('should build group by adding tightly connected chains', () => {
        // Start with C (Leaf). 
        // Should pull in B (Parent).
        // B should pull in A (Parent).
        // Assuming naive "add all neighbors" for this initial test or specifically parent/child.

        const group = layoutCalc._buildGroup(mockChains[2], mockChains, mockParents, mockChildren);

        const ids = Array.from(group).map(c => c.id);
        expect(ids).toContain('A');
        expect(ids).toContain('B');
        expect(ids).toContain('C');
    });

    it('should handle isolated chains (single node group)', () => {
        const isolatedChain = { id: 'Iso', startTime: 2000, endTime: 2010 };
        const group = layoutCalc._buildGroup(isolatedChain, [isolatedChain], new Map(), new Map());
        expect(group.size).toBe(1);
        expect(Array.from(group)[0].id).toBe('Iso');
    });
});
