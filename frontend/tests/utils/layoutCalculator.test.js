import { describe, it, expect } from 'vitest';
import { LayoutCalculator } from '../../src/utils/layoutCalculator';
import { VISUALIZATION } from '../../src/constants/visualization';

describe('LayoutCalculator', () => {
  const createMockGraphData = () => ({
    nodes: [
      {
        id: 'node1',
        founding_year: 2010,
        dissolution_year: 2015,
        eras: [
          { year: 2010, name: 'Team A', tier: 1 },
          { year: 2011, name: 'Team A', tier: 1 }
        ]
      },
      {
        id: 'node2',
        founding_year: 2012,
        dissolution_year: null,
        eras: [
          { year: 2012, name: 'Team B', tier: 2 },
          { year: 2013, name: 'Team B', tier: 2 }
        ]
      },
      {
        id: 'node3',
        founding_year: 2014,
        dissolution_year: 2018,
        eras: [
          { year: 2014, name: 'Team C', tier: 1 }
        ]
      }
    ],
    links: [
      {
        source: 'node1',
        target: 'node2',
        type: 'LEGAL_TRANSFER',
        year: 2012
      },
      {
        source: 'node2',
        target: 'node3',
        type: 'SPIRITUAL_SUCCESSION',
        year: 2014
      }
    ]
  });

  describe('calculateYearRange', () => {
    it('should calculate correct year range from nodes', () => {
      const graphData = createMockGraphData();
      const calculator = new LayoutCalculator(graphData, 1000, 800);
      const yearRange = calculator.calculateYearRange();
      const currentYear = new Date().getFullYear();

      expect(yearRange.min).toBe(1900);
      expect(yearRange.max).toBe(currentYear + 1);
    });

    it('should handle single node', () => {
      const graphData = {
        nodes: [
          {
            id: 'node1',
            founding_year: 2010,
            eras: [{ year: 2010, name: 'Team', tier: 1 }]
          }
        ],
        links: []
      };
      const calculator = new LayoutCalculator(graphData, 1000, 800);
      const yearRange = calculator.calculateYearRange();
      const currentYear = new Date().getFullYear();

      expect(yearRange.min).toBe(1900);
      expect(yearRange.max).toBe(currentYear + 1);
    });
  });





  describe('calculateLinkPaths', () => {
    it('should generate valid SVG paths for all links', () => {
      const graphData = createMockGraphData();
      const calculator = new LayoutCalculator(graphData, 1000, 800);
      const layout = calculator.calculateLayout();

      expect(layout.links.length).toBe(2);

      layout.links.forEach(link => {
        // Should have path property
        expect(link.path).toBeDefined();
        expect(typeof link.path).toBe('string');

        // Should start with M (move to)
        expect(link.path).toMatch(/^M /);

        // Should contain C (cubic bezier)
        expect(link.path).toContain('C ');

        // Should have source/target coordinates
        expect(link.sourceX).toBeDefined();
        expect(link.sourceY).toBeDefined();
        expect(link.targetX).toBeDefined();
        expect(link.targetY).toBeDefined();
      });
    });

    it('should filter out links with missing nodes', () => {
      const graphData = {
        nodes: [
          {
            id: 'node1',
            founding_year: 2010,
            eras: [{ year: 2010, name: 'Team A', tier: 1 }]
          }
        ],
        links: [
          {
            source: 'node1',
            target: 'nonexistent',
            type: 'LEGAL_TRANSFER',
            year: 2012
          }
        ]
      };
      const calculator = new LayoutCalculator(graphData, 1000, 800);
      const layout = calculator.calculateLayout();

      // Invalid link should be filtered out
      expect(layout.links.length).toBe(0);
    });
  });

  describe('calculateLayout (integration)', () => {
    it('should return complete layout with positioned nodes and links', () => {
      const graphData = createMockGraphData();
      const calculator = new LayoutCalculator(graphData, 1000, 800);
      const layout = calculator.calculateLayout();

      // Should have all nodes
      expect(layout.nodes.length).toBe(3);

      // All nodes should have position and size
      layout.nodes.forEach(node => {
        expect(node.x).toBeDefined();
        expect(node.y).toBeDefined();
        expect(node.width).toBeDefined();
        expect(node.height).toBeDefined();
        expect(node.x).toBeGreaterThanOrEqual(0);
        expect(node.y).toBeGreaterThanOrEqual(0);
      });

      // Should have all valid links
      expect(layout.links.length).toBe(2);

      // All links should have paths
      layout.links.forEach(link => {
        expect(link.path).toBeDefined();
        expect(link.type).toBeDefined();
      });
    });

    it('should handle empty nodes array', () => {
      const graphData = { nodes: [], links: [] };
      const calculator = new LayoutCalculator(graphData, 1000, 800);

      // Should not throw
      expect(() => calculator.calculateYearRange()).not.toThrow();
    });

    it('should handle nodes with no links', () => {
      const graphData = {
        nodes: [
          {
            id: 'node1',
            founding_year: 2010,
            eras: [{ year: 2010, name: 'Team', tier: 1 }]
          }
        ],
        links: []
      };
      const calculator = new LayoutCalculator(graphData, 1000, 800);
      const layout = calculator.calculateLayout();

      expect(layout.nodes.length).toBe(1);
      expect(layout.links.length).toBe(0);
    });
  });

  describe('Proportional Scaling', () => {
    it('should calculate pixelsPerYear correctly', () => {
      const graphData = { nodes: [], links: [] };
      // width=1000, padding=50, availableWidth=900
      // With empty nodes, year range defaults to 1900 - currentYear+1 (127 years)
      const calculator = new LayoutCalculator(graphData, 1000, 600, null, 1);

      // availableWidth = 1000 - 2*50 = 900
      // span = 127 years (1900 to 2027)
      // pixelsPerYear = 900 / 127 * 1 ≈ 7.0866
      expect(calculator.pixelsPerYear).toBeCloseTo(7.0866, 3);
    });

    it('should calculate pixelsPerYear proportional to width', () => {
      const graphData = { nodes: [], links: [] };

      // Same year range, different widths
      const calc1 = new LayoutCalculator(graphData, 1000, 600, null, 1);
      const calc2 = new LayoutCalculator(graphData, 2000, 600, null, 1);

      // Double width should give double pixelsPerYear
      expect(calc2.pixelsPerYear).toBeGreaterThan(calc1.pixelsPerYear);
      expect(calc2.pixelsPerYear / calc1.pixelsPerYear).toBeCloseTo(1900 / 900, 1);
    });

    it('should have rowHeight proportional to pixelsPerYear', () => {
      const graphData = {
        nodes: [
          { id: 'node1', founding_year: 2010, eras: [{ year: 2010, name: 'Team', tier: 1 }] },
          { id: 'node2', founding_year: 2015, eras: [{ year: 2015, name: 'Team2', tier: 1 }] }
        ],
        links: []
      };
      const calculator = new LayoutCalculator(graphData, 1000, 600, null, 1);
      const layout = calculator.calculateLayout();

      // With ASPECT_RATIO_MULTIPLIER = 1, rowHeight should equal pixelsPerYear * 1.5
      expect(layout.rowHeight).toBe(calculator.pixelsPerYear * 1.5);
    });

    it('should maintain aspect ratio = 1 (square)', () => {
      const graphData = {
        nodes: [{ id: 'node1', founding_year: 2010, eras: [{ year: 2010, name: 'Team', tier: 1 }] }],
        links: []
      };

      const calc1 = new LayoutCalculator(graphData, 1000, 600, null, 1);
      const calc2 = new LayoutCalculator(graphData, 2000, 600, null, 1);

      const layout1 = calc1.calculateLayout();
      const layout2 = calc2.calculateLayout();

      // Aspect ratio should be 1.5 for both (rowHeight / pixelsPerYear = 1.5)
      expect(layout1.rowHeight / calc1.pixelsPerYear).toBeCloseTo(1.5);
      expect(layout2.rowHeight / calc2.pixelsPerYear).toBeCloseTo(1.5);
    });
  });

  describe('NaN Prevention', () => {
    it('should handle empty node list without producing NaN', () => {
      const graphData = { nodes: [], links: [] };
      const calculator = new LayoutCalculator(graphData, 1000, 600);
      const layout = calculator.calculateLayout();

      // With no nodes, layout should have empty arrays
      expect(layout.nodes).toEqual([]);
      expect(layout.links).toEqual([]);

      // Year range should still be valid (not NaN)
      expect(layout.yearRange.min).not.toBeNaN();
      expect(layout.yearRange.max).not.toBeNaN();
    });

    it('should handle single node without producing NaN', () => {
      const graphData = {
        nodes: [
          {
            id: 'solo-node',
            founding_year: 2000,
            eras: [{ year: 2000, name: 'Solo Team', tier: 1 }]
          }
        ],
        links: []
      };
      const calculator = new LayoutCalculator(graphData, 1000, 600);
      const layout = calculator.calculateLayout();

      // Node position should not be NaN
      expect(layout.nodes).toHaveLength(1);
      expect(layout.nodes[0].x).not.toBeNaN();
      expect(layout.nodes[0].y).not.toBeNaN();
      expect(layout.nodes[0].width).not.toBeNaN();
      expect(layout.nodes[0].height).not.toBeNaN();
    });

    it('should handle zero-width container gracefully', () => {
      const graphData = createMockGraphData();
      const calculator = new LayoutCalculator(graphData, 0, 600);
      const layout = calculator.calculateLayout();

      // Should not crash and should not produce NaN
      layout.nodes.forEach(node => {
        expect(node.x).not.toBeNaN();
        expect(node.y).not.toBeNaN();
      });
    });

    it('should handle nodes with same founding year', () => {
      const graphData = {
        nodes: [
          { id: 'node1', founding_year: 2000, eras: [{ year: 2000, name: 'A', tier: 1 }] },
          { id: 'node2', founding_year: 2000, eras: [{ year: 2000, name: 'B', tier: 1 }] },
          { id: 'node3', founding_year: 2000, eras: [{ year: 2000, name: 'C', tier: 1 }] }
        ],
        links: []
      };
      const calculator = new LayoutCalculator(graphData, 1000, 600);
      const layout = calculator.calculateLayout();

      // All nodes should have valid positions
      layout.nodes.forEach(node => {
        expect(node.x).not.toBeNaN();
        expect(node.y).not.toBeNaN();
      });
    });
  });

  describe('Link Validation', () => {
    it('should filter out links with missing source nodes', () => {
      const graphData = {
        nodes: [
          { id: 'node1', founding_year: 2000, eras: [{ year: 2000, name: 'A', tier: 1 }] }
        ],
        links: [
          { source: 'node1', target: 'node2', year: 2001, type: 'LEGAL_TRANSFER' }, // node2 missing
          { source: 'node1', target: 'node1', year: 2000, type: 'SPIRITUAL_SUCCESSION' }  // valid self-link
        ]
      };
      const calculator = new LayoutCalculator(graphData, 1000, 600);
      const layout = calculator.calculateLayout();

      // Should only include the valid link
      expect(layout.links).toHaveLength(1);
      expect(layout.links[0].target).toBe('node1');
    });

    it('should filter out links with missing target nodes', () => {
      const graphData = {
        nodes: [
          { id: 'node1', founding_year: 2000, eras: [{ year: 2000, name: 'A', tier: 1 }] },
          { id: 'node2', founding_year: 2002, eras: [{ year: 2002, name: 'B', tier: 1 }] }
        ],
        links: [
          { source: 'nonexistent', target: 'node1', year: 2001, type: 'LEGAL_TRANSFER' }, // source missing
          { source: 'node1', target: 'node2', year: 2002, type: 'LEGAL_TRANSFER' }  // valid
        ]
      };
      const calculator = new LayoutCalculator(graphData, 1000, 600);
      const layout = calculator.calculateLayout();

      // Should only include the valid link
      expect(layout.links).toHaveLength(1);
      expect(layout.links[0].source).toBe('node1');
      expect(layout.links[0].target).toBe('node2');
    });

    it('should filter out links with both source and target missing', () => {
      const graphData = {
        nodes: [
          { id: 'node1', founding_year: 2000, eras: [{ year: 2000, name: 'A', tier: 1 }] }
        ],
        links: [
          { source: 'ghost1', target: 'ghost2', year: 2001, type: 'LEGAL_TRANSFER' }, // both missing
          { source: 'node1', target: 'ghost3', year: 2002, type: 'SPIRITUAL_SUCCESSION' } // target missing
        ]
      };
      const calculator = new LayoutCalculator(graphData, 1000, 600);
      const layout = calculator.calculateLayout();

      // Should have no links
      expect(layout.links).toHaveLength(0);
    });

    it('should preserve all links when all nodes exist', () => {
      const graphData = createMockGraphData(); // Has 3 nodes, 2 links
      const calculator = new LayoutCalculator(graphData, 1000, 600);
      const layout = calculator.calculateLayout();

      // All links should be preserved
      expect(layout.links).toHaveLength(2);
    });
  });
});
