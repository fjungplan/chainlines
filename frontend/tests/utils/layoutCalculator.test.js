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
});
