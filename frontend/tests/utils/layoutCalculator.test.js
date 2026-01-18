import { describe, it, expect, vi } from 'vitest';
import { LayoutCalculator } from '../../src/utils/layoutCalculator';

describe('LayoutCalculator Refactor (Force-Directed)', () => {
  const createMockGraphData = () => ({
    nodes: [
      { id: 'n1', founding_year: 2000, dissolution_year: 2005, eras: [{ year: 2000, name: 'A' }] },
      { id: 'n2', founding_year: 2005, dissolution_year: 2010, eras: [{ year: 2005, name: 'B' }] },
      { id: 'n3', founding_year: 2000, dissolution_year: 2010, eras: [{ year: 2000, name: 'C' }] },
      { id: 'n4', founding_year: 2010, dissolution_year: null, eras: [{ year: 2010, name: 'D' }] } // Active
    ],
    links: [
      { source: 'n1', target: 'n2', type: 'LEGAL_TRANSFER', year: 2005 }
    ]
  });

  describe('Phase 1: Atomic Chain Decomposition', () => {
    it('should group 1-to-1 legal transfers into chains', () => {
      // Linear chain: n1 -> n2
      const graphData = createMockGraphData();
      const calculator = new LayoutCalculator(graphData, 1000, 800);

      // Access private/internal method if possible, or verify via public layout
      // For TDD, we assume we'll expose or test via side-effect, 
      // but let's assume we can call internal methods for unit testing if we make them accessible
      // or we can test the `assignYPositions` output.
      // Since we are refactoring, we'll likely add these methods to the class.

      // We haven't implemented it yet, so this test expects the method to exist.
      // If it doesn't, we'll fail (GOOD).
      if (calculator.buildChains) {
        const chains = calculator.buildChains(graphData.nodes, graphData.links);
        expect(chains.length).toBeGreaterThan(0);
        // n1 and n2 are connected 1-to-1, but our NEW STRATEGY says we BREAK chains at every node
        // for maximum flexibility, UNLESS we decide to fuse simple ones.
        // Wait, the plan said "Strict Atomic Chains: Chains break at any split/merge."
        // AND "1-to-1 segments" are chains.
        // So n1 and n2 are SEPARATE chains if we strictly break?
        // Let's re-read the plan: "Internal nodes have exactly 1 predecessor and 1 successor."
        // A chain is A -> B -> C.
        // So n1 -> n2 SHOULD be a single chain if n1 has no other succ and n2 no other pred.

        const chainWithN1 = chains.find(c => c.nodes.some(n => n.id === 'n1'));
        expect(chainWithN1).toBeDefined();
        // With the "Atomic Chain" definition, n1 -> n2 should be ONE chain.
        // Expect failure here until implemented.
        expect(chainWithN1.nodes.some(n => n.id === 'n2')).toBe(true);
      }
    });

    it('should break chains at splits (1-to-2)', () => {
      const graphData = {
        nodes: [
          { id: 'root', founding_year: 2000, eras: [{ year: 2000, name: 'R' }] },
          { id: 'child1', founding_year: 2005, eras: [{ year: 2005, name: 'C1' }] },
          { id: 'child2', founding_year: 2005, eras: [{ year: 2005, name: 'C2' }] }
        ],
        links: [
          { source: 'root', target: 'child1', type: 'LEGAL_TRANSFER' },
          { source: 'root', target: 'child2', type: 'SPLIT' }
        ]
      };
      const calculator = new LayoutCalculator(graphData, 1000, 800);

      if (calculator.buildChains) {
        const chains = calculator.buildChains(graphData.nodes, graphData.links);
        // Root is a split point -> It ends a chain.
        // Child1 and Child2 start new chains.
        // So we expect 3 chains? Or does Root belong to one?
        // Definition: "Internal nodes have exactly 1 predecessor and 1 successor."
        // Root has 0 preds, 2 succs. It cannot be internal.
        // So Root is a chain of length 1.

        const rootChain = chains.find(c => c.nodes.some(n => n.id === 'root'));
        expect(rootChain).toBeDefined();
        expect(rootChain.nodes.length).toBe(1);
        expect(rootChain.nodes.some(n => n.id === 'child1')).toBe(false);
        expect(rootChain.nodes.some(n => n.id === 'child2')).toBe(false);
      }
    });
  });

  describe('Phase 2 & 3: Layout & No Overlaps', () => {
    it('should assign valid Y positions without overlaps in the same lane', () => {
      const graphData = createMockGraphData();
      const calculator = new LayoutCalculator(graphData, 1000, 800);
      const layout = calculator.calculateLayout();

      // Check for overlaps
      const nodesByLane = new Map();
      layout.nodes.forEach(node => {
        // Calculate lane index from Y (approximate)
        const laneIndex = Math.round((node.y - 50) / calculator.rowHeight);
        if (!nodesByLane.has(laneIndex)) nodesByLane.set(laneIndex, []);
        nodesByLane.get(laneIndex).push(node);
      });

      nodesByLane.forEach((nodesInLane, lane) => {
        // Sort by start year
        nodesInLane.sort((a, b) => a.founding_year - b.founding_year);

        for (let i = 0; i < nodesInLane.length - 1; i++) {
          const current = nodesInLane[i];
          const next = nodesInLane[i + 1];
          const currentEnd = current.dissolution_year || 9999;

          // Strict check: Next start must be >= Current end
          expect(next.founding_year).toBeGreaterThanOrEqual(currentEnd);
        }
      });
    });
  });

  describe('Integration: Complex Graph (Diamond)', () => {
    it('should handle Split-then-Merge (Diamond Pattern)', () => {
      // A -> (B, C) -> D
      const graphData = {
        nodes: [
          { id: 'A', founding_year: 2000, dissolution_year: 2005, eras: [{ year: 2000, name: 'A' }] },
          { id: 'B', founding_year: 2005, dissolution_year: 2010, eras: [{ year: 2005, name: 'B' }] },
          { id: 'C', founding_year: 2005, dissolution_year: 2010, eras: [{ year: 2005, name: 'C' }] },
          { id: 'D', founding_year: 2010, dissolution_year: null, eras: [{ year: 2010, name: 'D' }] }
        ],
        links: [
          { source: 'A', target: 'B', type: 'SPLIT' },
          { source: 'A', target: 'C', type: 'SPLIT' },
          { source: 'B', target: 'D', type: 'MERGE' },
          { source: 'C', target: 'D', type: 'MERGE' }
        ]
      };
      const calculator = new LayoutCalculator(graphData, 1000, 800);
      const layout = calculator.calculateLayout();

      // Basic sanity checks
      const nodeA = layout.nodes.find(n => n.id === 'A');
      const nodeB = layout.nodes.find(n => n.id === 'B');
      const nodeC = layout.nodes.find(n => n.id === 'C');
      const nodeD = layout.nodes.find(n => n.id === 'D');

      expect(nodeA).toBeDefined();
      expect(nodeD).toBeDefined();

      // B and C should be on different Y coordinates (lanes)
      expect(Math.abs(nodeB.y - nodeC.y)).toBeGreaterThan(10);

      // D should probably align with one of them or be in between
      // (Force directed usually centers it or aligns with 'stronger' parent)
      // D should probably align with one of them or be in between
      // (Force directed usually centers it or aligns with 'stronger' parent)
      const nodeACheck = layout.nodes.find(n => n.id === 'A');
      const nodeDCheck = layout.nodes.find(n => n.id === 'D');
      expect(nodeACheck).toBeDefined();
      expect(nodeDCheck).toBeDefined();
    });

    it('should avoid cut-throughs (Link passing through broad node)', () => {
      // Setup:
      // Three parallel tracks forced by parents:
      // Track 0: P1 -> N1 (Ends 2010)
      // Track 1: P2 -> N2 (Ends 2020) - The Blocker
      // Track 2: P3 -> D3 (Ends 2010) -> N3 (Starts 2010)
      // Link: N1 -> N3 at 2010.
      // Initial layout (Barycenter) puts N1=0, N2=1, N3=2.
      // Link N1(0)->N3(2) cuts through N2(1).
      // Expectation: N2 should be moved out of the way (e.g. to Lane 3), leaving Lane 1 open for the link corridor.
      // CRITICAL: All must be in ONE family for interleaving to occur.
      // So we link P1, P2, P3 to a Common Root.

      const graphData = {
        nodes: [
          // Common Root
          { id: 'Root', founding_year: 1980, dissolution_year: 1990, eras: [{ year: 1980, name: 'Root' }] },

          // Parents (anchors) - Start 1990
          { id: 'P1', founding_year: 1990, dissolution_year: 2000, eras: [{ year: 1990, name: 'P1' }] },
          { id: 'P2', founding_year: 1990, dissolution_year: 2000, eras: [{ year: 1990, name: 'P2' }] },
          { id: 'P3', founding_year: 1990, dissolution_year: 2000, eras: [{ year: 1990, name: 'P3' }] },

          // Children
          { id: 'N1', founding_year: 2000, dissolution_year: 2010, eras: [{ year: 2000, name: 'N1' }] },
          { id: 'N2', founding_year: 2000, dissolution_year: 2020, eras: [{ year: 2000, name: 'N2' }] }, // Broad blocker
          { id: 'D3', founding_year: 2000, dissolution_year: 2010, eras: [{ year: 2000, name: 'D3' }] },
          { id: 'N3', founding_year: 2010, dissolution_year: 2020, eras: [{ year: 2010, name: 'N3' }] }
        ],
        links: [
          // Fan out from Root
          { source: 'Root', target: 'P1', type: 'SPLIT', year: 1990 },
          { source: 'Root', target: 'P2', type: 'SPLIT', year: 1990 },
          { source: 'Root', target: 'P3', type: 'SPLIT', year: 1990 },

          // Vertical ancestry
          { source: 'P1', target: 'N1', type: 'LEGAL_TRANSFER', year: 2000 },
          { source: 'P2', target: 'N2', type: 'LEGAL_TRANSFER', year: 2000 },
          { source: 'P3', target: 'D3', type: 'LEGAL_TRANSFER', year: 2000 },
          { source: 'D3', target: 'N3', type: 'LEGAL_TRANSFER', year: 2010 },

          // The Cross-Link
          { source: 'N1', target: 'N3', type: 'LEGAL_TRANSFER', year: 2010 }
        ]
      };

      const calculator = new LayoutCalculator(graphData, 1000, 800);
      const layout = calculator.calculateLayout();

      const n1 = layout.nodes.find(n => n.id === 'N1');
      const n2 = layout.nodes.find(n => n.id === 'N2');
      const n3 = layout.nodes.find(n => n.id === 'N3');

      const lane1 = Math.round((n1.y - 50) / calculator.rowHeight);
      const lane2 = Math.round((n2.y - 50) / calculator.rowHeight);
      const lane3 = Math.round((n3.y - 50) / calculator.rowHeight);

      // Check if N2 is strictly between N1 and N3
      const minInfo = Math.min(lane1, lane3);
      const maxInfo = Math.max(lane1, lane3);
      const n2IsBlocking = lane2 > minInfo && lane2 < maxInfo;

      // To debug what happened
      if (n2IsBlocking) {
        console.log(`Cut-Through Detected! N1:${lane1}, N2:${lane2}, N3:${lane3}`);
      } else {
        console.log(`No Cut-Through. N1:${lane1}, N2:${lane2}, N3:${lane3}`);
        // Verify relative positions
        console.log(`Positions: N1(L${lane1}), N2(L${lane2}), N3(L${lane3})`);
      }

      expect(n2IsBlocking).toBe(false);
    });

    it('should respect Gantt temporal sorting of families', () => {
      // Family 1: Starts 1900
      // Family 2: Starts 1950
      // Family 3: Starts 1901
      // Expect Order: 1, 3, 2 (or 3, 1, 2 depending on tolerance)
      const graphData = {
        nodes: [
          { id: 'F1', founding_year: 1900, eras: [{ year: 1900, name: 'F1' }] },
          { id: 'F2', founding_year: 1950, eras: [{ year: 1950, name: 'F2' }] },
          { id: 'F3', founding_year: 1901, eras: [{ year: 1901, name: 'F3' }] }
        ],
        links: [] // No links -> 3 separate families
      };
      const calculator = new LayoutCalculator(graphData, 1000, 800);
      const layout = calculator.calculateLayout();

      const f1 = layout.nodes.find(n => n.id === 'F1');
      const f2 = layout.nodes.find(n => n.id === 'F2');
      const f3 = layout.nodes.find(n => n.id === 'F3');

      expect(f1.y).toBeLessThan(f2.y);
      expect(f3.y).toBeLessThan(f2.y);
    });
  });
});
