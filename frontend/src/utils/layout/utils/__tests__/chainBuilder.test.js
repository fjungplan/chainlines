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
            { source: 'aki', target: 'vini', event_year: 1998 },
            { source: 'amica', target: 'vini', event_year: 2001 }
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
});
