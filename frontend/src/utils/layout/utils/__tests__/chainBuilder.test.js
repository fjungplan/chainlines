import { describe, it, expect } from 'vitest';
import { buildChains } from '../chainBuilder';

describe('chainBuilder - Merge Logic Alignment', () => {
    it('should continue chain through a merge if a single Primary Predecessor exists', () => {
        // Setup matches the Aki-Safi / Vini Caldirola scenario
        // Aki-Safi (1995-1997) -> Vini (1998)
        // Amica Chips (1997-2000) -> Vini (2001) [Late merger]

        const nodes = [
            {
                id: 'aki',
                legal_name: 'Aki - Safi',
                founding_year: 1995,
                dissolution_year: 1997
            },
            {
                id: 'amica',
                legal_name: 'Amica Chips',
                founding_year: 1997,
                dissolution_year: 2000
            },
            {
                id: 'vini',
                legal_name: 'Vini Caldirola',
                founding_year: 1998,
                dissolution_year: 2004
            }
        ];

        const links = [
            { source: 'aki', target: 'vini', event_year: 1998, event_type: 'LEGAL_TRANSFER' },
            { source: 'amica', target: 'vini', event_year: 2001, event_type: 'SPIRITUAL_SUCCESSION' }
        ];

        // Original logic: Breaks at ANY merge (node with >1 predecessors)
        // New logic: Should see Aki -> Vini as "Primary" (1998 link to 1998 start)
        const chains = buildChains(nodes, links);

        // Find chain containing Aki
        const akiChain = chains.find(c => c.nodes.some(n => n.id === 'aki'));
        expect(akiChain).toBeDefined();

        // Verify Vini is in the SAME chain as Aki
        const hasVini = akiChain.nodes.some(n => n.id === 'vini');

        // This expectation ensures we align with backend logic
        expect(hasVini).toBe(true);
        expect(akiChain.nodes.length).toBe(2); // Aki, Vini
    });

    it('should break chain if NO single Primary Predecessor exists (Ambiguous Merge)', () => {
        // Setup: Two potential parents, both linking at founding year
        const nodes = [
            { id: 'p1', founding_year: 1990, dissolution_year: 1995 },
            { id: 'p2', founding_year: 1990, dissolution_year: 1995 },
            { id: 'child', founding_year: 1995, dissolution_year: 2000 }
        ];

        const links = [
            { source: 'p1', target: 'child', event_year: 1995 },
            { source: 'p2', target: 'child', event_year: 1995 }
        ];

        const chains = buildChains(nodes, links);

        // Child should start its own new chain
        const childChain = chains.find(c => c.nodes[0].id === 'child');
        expect(childChain).toBeDefined();
        expect(childChain.nodes.length).toBe(1);
    });

    it('should continue chain through a 1:1 link no matter the type (Rule 1)', () => {
        const nodes = [
            { id: 'a', founding_year: 1990, dissolution_year: 1995 },
            { id: 'b', founding_year: 1996, dissolution_year: 2000 }
        ];
        const links = [
            { source: 'a', target: 'b', event_year: 1996, event_type: 'SPIRITUAL_SUCCESSION' }
        ];

        const chains = buildChains(nodes, links);

        const aChain = chains.find(c => c.nodes.some(n => n.id === 'a'));
        expect(aChain.nodes.some(n => n.id === 'b')).toBe(true);
        expect(aChain.nodes.length).toBe(2);
    });

    it('should break on split if multiple successors exist and zero are LEGAL_TRANSFER', () => {
        const nodes = [
            { id: 'parent', founding_year: 1990, dissolution_year: 1995 },
            { id: 'child1', founding_year: 1996, dissolution_year: 2000 },
            { id: 'child2', founding_year: 1996, dissolution_year: 2000 }
        ];
        const links = [
            { source: 'parent', target: 'child1', event_year: 1996, event_type: 'SPLIT' },
            { source: 'parent', target: 'child2', event_year: 1996, event_type: 'SPIRITUAL_SUCCESSION' }
        ];

        const chains = buildChains(nodes, links);

        const parentChain = chains.find(c => c.nodes[0].id === 'parent');
        expect(parentChain.nodes.length).toBe(1);
        expect(chains.length).toBe(3);
    });
});
