import { describe, it, expect } from 'vitest';
import { buildFamilies, buildChains } from '../../../src/utils/layout/utils/chainBuilder';

describe('chainBuilder', () => {
    describe('buildChains', () => {
        // Helper to create nodes
        const createNode = (id, founding = 2000, dissolution = null) => ({
            id,
            founding_year: founding,
            dissolution_year: dissolution,
            eras: [{ year: founding }]
        });

        it('should create individual chains for isolated nodes', () => {
            const nodes = [createNode('A'), createNode('B')];
            const links = [];
            const chains = buildChains(nodes, links);

            expect(chains).toHaveLength(2);
            expect(chains[0].nodes).toHaveLength(1);
            expect(chains[0].nodes[0].id).toBe('A');
            expect(chains[1].nodes).toHaveLength(1);
        });

        it('should chain nodes with 1:1 relationship', () => {
            const nodes = [createNode('A', 2000), createNode('B', 2010)];
            const links = [{ source: 'A', target: 'B' }];
            const chains = buildChains(nodes, links);

            expect(chains).toHaveLength(1);
            expect(chains[0].nodes).toHaveLength(2);
            expect(chains[0].nodes[0].id).toBe('A');
            expect(chains[0].nodes[1].id).toBe('B');
        });

        it('should break chains on visual overlap (Dirty Data)', () => {
            // A ends 2015, B starts 2010. Overlap!
            const nodes = [createNode('A', 2000, 2015), createNode('B', 2010)];
            const links = [{ source: 'A', target: 'B' }];
            const chains = buildChains(nodes, links);

            expect(chains).toHaveLength(2); // Should be broken
            expect(chains[0].nodes[0].id).toBe('A');
            expect(chains[1].nodes[0].id).toBe('B');
        });

        it('should break chains on splits (1 parent, 2 children)', () => {
            const nodes = [createNode('A'), createNode('B1'), createNode('B2')];
            const links = [
                { source: 'A', target: 'B1' },
                { source: 'A', target: 'B2' }
            ];
            const chains = buildChains(nodes, links);

            // A (1), B1 (1), B2 (1) = 3 chains
            expect(chains).toHaveLength(3);
        });

        it('should break chains on merges (2 parents, 1 child)', () => {
            const nodes = [createNode('A1'), createNode('A2'), createNode('B')];
            const links = [
                { source: 'A1', target: 'B' },
                { source: 'A2', target: 'B' }
            ];
            const chains = buildChains(nodes, links);

            // A1, A2, B = 3 chains
            expect(chains).toHaveLength(3);
        });
    });

    describe('buildFamilies', () => {
        // Helper to create chains
        const createChain = (id, startTime = 2000, nodes = []) => ({
            id,
            startTime,
            nodes: nodes.map(nId => ({ id: nId }))
        });

        it('should return empty families for empty input', () => {
            const chains = [];
            const links = [];
            const families = buildFamilies(chains, links);
            expect(families).toEqual([]);
        });

        it('should group connected chains into a single family', () => {
            // A -- B -- C
            const c1 = createChain('A', 2000, ['n1']);
            const c2 = createChain('B', 2005, ['n2']);
            const c3 = createChain('C', 2010, ['n3']);
            const chains = [c1, c2, c3];

            const links = [
                { source: 'n1', target: 'n2' },
                { source: 'n2', target: 'n3' }
            ];

            const families = buildFamilies(chains, links);

            expect(families).toHaveLength(1);
            expect(families[0].chains).toHaveLength(3);
            expect(families[0].chains).toContain(c1);
            expect(families[0].chains).toContain(c2);
            expect(families[0].chains).toContain(c3);
        });

        it('should separate disconnected subgraphs', () => {
            // A -- B    C -- D
            const cA = createChain('A', 2000, ['nA']);
            const cB = createChain('B', 2001, ['nB']);
            const cC = createChain('C', 2005, ['nC']);
            const cD = createChain('D', 2006, ['nD']);
            const chains = [cA, cB, cC, cD];

            const links = [
                { source: 'nA', target: 'nB' },
                { source: 'nC', target: 'nD' }
            ];

            const families = buildFamilies(chains, links);

            expect(families).toHaveLength(2);

            // Sort to ensure stable assertions
            families.sort((a, b) => a.minStart - b.minStart);

            expect(families[0].chains).toHaveLength(2); // A-B
            expect(families[0].chains.map(c => c.id)).toContain('A');
            expect(families[0].chains.map(c => c.id)).toContain('B');

            expect(families[1].chains).toHaveLength(2); // C-D
            expect(families[1].chains.map(c => c.id)).toContain('C');
            expect(families[1].chains.map(c => c.id)).toContain('D');
        });

        it('should calculate minStart for each family', () => {
            const c1 = createChain('A', 2010, ['n1']);
            const c2 = createChain('B', 2005, ['n2']); // Earliest in family
            const chains = [c1, c2];
            const links = [{ source: 'n1', target: 'n2' }]; // Connected

            const families = buildFamilies(chains, links);

            expect(families).toHaveLength(1);
            expect(families[0].minStart).toBe(2005);
        });

        it('should sort families by start year', () => {
            // Family 1: Starts 2010
            const f1c1 = createChain('F1', 2010, ['f1']);
            // Family 2: Starts 2000
            const f2c1 = createChain('F2', 2000, ['f2']);

            const chains = [f1c1, f2c1];
            const links = []; // No links, distinct families

            const families = buildFamilies(chains, links);

            expect(families).toHaveLength(2);
            expect(families[0].minStart).toBe(2000); // F2 first
            expect(families[1].minStart).toBe(2010); // F1 second
        });

        it('should use family size as tie-breaker (largest first)', () => {
            // Family 1: Size 2, Start 2000
            const f1c1 = createChain('F1A', 2000, ['f1a']);
            const f1c2 = createChain('F1B', 2001, ['f1b']);

            // Family 2: Size 1, Start 2000
            const f2c1 = createChain('F2A', 2000, ['f2a']);

            const chains = [f1c1, f1c2, f2c1];
            const links = [{ source: 'f1a', target: 'f1b' }];

            const families = buildFamilies(chains, links);

            expect(families).toHaveLength(2);
            // Both start at 2000. Largest (size 2) should be first.
            expect(families[0].chains).toHaveLength(2);
            expect(families[1].chains).toHaveLength(1);
        });
    });
});
