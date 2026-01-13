import { describe, it, expect } from 'vitest';

/**
 * Tests for lineage finding logic
 * These tests verify the algorithm for finding all connected nodes
 * in a team's lineage (predecessors and successors)
 */
describe('TimelineGraph - Lineage Finding', () => {
    describe('findLineage', () => {
        const createMockData = () => ({
            nodes: [
                { id: '7up', name: '7UP - Colorado Cyclist' },
                { id: 'predecessor', name: 'Predecessor Team' },
                { id: 'successor', name: 'Successor Team' },
                { id: 'successor2', name: 'Second Successor' },
                { id: 'unrelated', name: 'Unrelated Team' },
                { id: 'another-unrelated', name: 'Another Unrelated' }
            ],
            links: [
                { source: 'predecessor', target: '7up', year: 1997 },
                { source: '7up', target: 'successor', year: 2003 },
                { source: 'successor', target: 'successor2', year: 2010 }
            ]
        });

        it('finds direct predecessor', () => {
            const { nodes, links } = createMockData();
            const selectedNode = nodes.find(n => n.id === '7up');

            // The lineage should include: predecessor, 7up, successor, successor2
            const lineage = findLineage(selectedNode, nodes, links);

            expect(lineage.has('predecessor')).toBe(true);
            expect(lineage.has('7up')).toBe(true);
        });

        it('finds direct successor', () => {
            const { nodes, links } = createMockData();
            const selectedNode = nodes.find(n => n.id === '7up');

            const lineage = findLineage(selectedNode, nodes, links);

            expect(lineage.has('successor')).toBe(true);
        });

        it('finds transitive successors (multi-hop)', () => {
            const { nodes, links } = createMockData();
            const selectedNode = nodes.find(n => n.id === '7up');

            const lineage = findLineage(selectedNode, nodes, links);

            // Should find successor2 even though it's 2 hops away
            expect(lineage.has('successor2')).toBe(true);
        });

        it('excludes unrelated teams', () => {
            const { nodes, links } = createMockData();
            const selectedNode = nodes.find(n => n.id === '7up');

            const lineage = findLineage(selectedNode, nodes, links);

            expect(lineage.has('unrelated')).toBe(false);
            expect(lineage.has('another-unrelated')).toBe(false);
        });

        it('includes the selected node itself', () => {
            const { nodes, links } = createMockData();
            const selectedNode = nodes.find(n => n.id === '7up');

            const lineage = findLineage(selectedNode, nodes, links);

            expect(lineage.has('7up')).toBe(true);
        });

        it('returns correct lineage size for 7UP test case', () => {
            const { nodes, links } = createMockData();
            const selectedNode = nodes.find(n => n.id === '7up');

            const lineage = findLineage(selectedNode, nodes, links);

            // Should be 4: predecessor, 7up, successor, successor2
            expect(lineage.size).toBe(4);
        });

        it('handles node with no connections', () => {
            const { nodes, links } = createMockData();
            const selectedNode = nodes.find(n => n.id === 'unrelated');

            const lineage = findLineage(selectedNode, nodes, links);

            // Should only contain itself
            expect(lineage.size).toBe(1);
            expect(lineage.has('unrelated')).toBe(true);
        });

        it('handles bidirectional search correctly', () => {
            const nodes = [
                { id: 'a', name: 'A' },
                { id: 'b', name: 'B' },
                { id: 'c', name: 'C' }
            ];
            const links = [
                { source: 'a', target: 'b', year: 2000 },
                { source: 'b', target: 'c', year: 2005 }
            ];

            // Select middle node
            const selectedNode = nodes.find(n => n.id === 'b');
            const lineage = findLineage(selectedNode, nodes, links);

            // Should find both predecessor (a) and successor (c)
            expect(lineage.has('a')).toBe(true);
            expect(lineage.has('b')).toBe(true);
            expect(lineage.has('c')).toBe(true);
            expect(lineage.size).toBe(3);
        });
    });
});

/**
 * Helper function to find lineage
 * This will be implemented in TimelineGraph.jsx
 * Exported here for testing purposes
 */
function findLineage(selectedNode, allNodes, allLinks) {
    if (!selectedNode) return new Set();

    const lineageSet = new Set([selectedNode.id]);
    const queue = [selectedNode.id];

    while (queue.length > 0) {
        const currentId = queue.shift();

        // Find all connected links
        allLinks.forEach(link => {
            if (link.source === currentId && !lineageSet.has(link.target)) {
                lineageSet.add(link.target);
                queue.push(link.target);
            }
            if (link.target === currentId && !lineageSet.has(link.source)) {
                lineageSet.add(link.source);
                queue.push(link.source);
            }
        });
    }

    return lineageSet;
}

// Export for use in implementation
export { findLineage };
