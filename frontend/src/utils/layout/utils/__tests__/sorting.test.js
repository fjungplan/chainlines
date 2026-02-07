
import { describe, it, expect, vi } from 'vitest';
import { buildFamilies, buildChains, getEndYear } from '../chainBuilder';

describe('Timeline Sorting Logic', () => {

    describe('getEndYear Logic (Zombie Detection)', () => {
        const currentYear = new Date().getFullYear();

        it('should return dissolution_year if present', () => {
            const node = { id: 'A', dissolution_year: 2005 };
            // Note: Since current chainBuilder.js doesn't export getEndYear directly, 
            // we might need to test it implicitly or export it. 
            // For TDD, we assume we WILL export it.
            expect(getEndYear(node)).toBe(2005);
        });

        it('should return last era year if no dissolution_year and last era < current', () => {
            const node = {
                id: 'B',
                dissolution_year: null,
                eras: [{ year: 1990 }, { year: 1995 }] // Last era 1995
            };
            expect(getEndYear(node)).toBe(1995);
        });

        it('should return current year if no dissolution_year and last era >= current - 1', () => {
            // Simulating active team
            const node = {
                id: 'C',
                dissolution_year: null,
                eras: [{ year: 2020 }, { year: currentYear }]
            };
            expect(getEndYear(node)).toBe(currentYear);
        });

        it('should return current year if no dissolution_year and no eras (fallback)', () => {
            const node = { id: 'D', dissolution_year: null, eras: [] };
            expect(getEndYear(node)).toBe(currentYear);
        });
    });

    describe('Family Sorting (buildFamilies)', () => {
        // Mock chains with distinct Start/End orders
        // Chain A: 2000-2010 (Mid Start, Mid End)
        const chainA = { id: 'A', startTime: 2000, endTime: 2010, nodes: [{ id: 'A' }] };
        // Chain B: 1990-2020 (Early Start, Late End)
        const chainB = { id: 'B', startTime: 1990, endTime: 2020, nodes: [{ id: 'B' }] };
        // Chain C: 2005-2008 (Late Start, Early End)
        const chainC = { id: 'C', startTime: 2005, endTime: 2008, nodes: [{ id: 'C' }] };

        const chains = [chainA, chainB, chainC];
        const links = []; // No links, so each chain is a family

        it('should sort families by Start Year ASC (default)', () => {
            const families = buildFamilies(chains, links, 'START');
            // Expected Start Order: B (1990), A (2000), C (2005)
            expect(families[0].chains[0].id).toBe('B');
            expect(families[1].chains[0].id).toBe('A');
            expect(families[2].chains[0].id).toBe('C');
        });

        it('should sort families by End Year ASC', () => {
            const families = buildFamilies(chains, links, 'END');
            // Expected End Order: C (2008), A (2010), B (2020)
            expect(families[0].chains[0].id).toBe('C');
            expect(families[1].chains[0].id).toBe('A');
            expect(families[2].chains[0].id).toBe('B');
        });
    });

    describe('Secondary Sorting Criteria', () => {
        // Test Case 1: Start Mode -> Same Start, Different End
        const familySameStart1 = { chains: [{ id: 'S1', endTime: 2020, startTime: 2000 }], minStart: 2000, maxEnd: 2020 };
        const familySameStart2 = { chains: [{ id: 'S2', endTime: 2010, startTime: 2000 }], minStart: 2000, maxEnd: 2010 };

        // Test Case 2: End Mode -> Same End, Different Start
        const familySameEnd1 = { chains: [{ id: 'E1', startTime: 2000, endTime: 2020 }], minStart: 2000, maxEnd: 2020 };
        const familySameEnd2 = { chains: [{ id: 'E2', startTime: 1990, endTime: 2020 }], minStart: 1990, maxEnd: 2020 };

        // Mock chains array for testing sort explicitly since buildFamilies internal sort is what we want to test.
        // However, buildFamilies takes raw chains and builds families. 
        // We need raw chains that produce families with these properties.

        it('should sort by Earliest End Year (ASC) when Start Years are equal (Start Mode)', () => {
            const chainS1 = { id: 'S1', startTime: 2000, endTime: 2020, nodes: [{ id: 'S1' }] };
            const chainS2 = { id: 'S2', startTime: 2000, endTime: 2010, nodes: [{ id: 'S2' }] };
            const families = buildFamilies([chainS1, chainS2], [], 'START');

            // Expect S2 (End 2010) before S1 (End 2020)
            expect(families[0].chains[0].id).toBe('S2');
            expect(families[1].chains[0].id).toBe('S1');
        });

        it('should sort by Earliest Start Year (ASC) when End Years are equal (End Mode)', () => {
            const chainE1 = { id: 'E1', startTime: 2000, endTime: 2020, nodes: [{ id: 'E1' }] };
            const chainE2 = { id: 'E2', startTime: 1990, endTime: 2020, nodes: [{ id: 'E2' }] };
            const families = buildFamilies([chainE1, chainE2], [], 'END');

            // Expect E2 (Start 1990) before E1 (Start 2000)
            expect(families[0].chains[0].id).toBe('E2');
            expect(families[1].chains[0].id).toBe('E1');
        });
    });
});
