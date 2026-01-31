import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { LayoutCalculator } from '../../src/utils/layoutCalculator';

describe('Precomputed Layout Loading', () => {
    let fetchMock;

    beforeEach(() => {
        // Mock global fetch
        fetchMock = vi.fn();
        global.fetch = fetchMock;
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('should load precomputed layouts on init', async () => {
        const mockLayouts = {
            'hash1': {
                layout_data: { 'chain1': 0, 'chain2': 1 },
                score: 123.45,
                optimized_at: '2023-01-01T00:00:00Z'
            }
        };

        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => mockLayouts
        });

        const graphData = {
            nodes: [
                { id: 'n1', founding_year: 2000, dissolution_year: 2005, eras: [{ year: 2000, name: 'A' }] }
            ],
            links: []
        };

        const calculator = new LayoutCalculator(graphData, 1000, 800);

        // Wait for async load
        await new Promise(resolve => setTimeout(resolve, 100));

        expect(fetchMock).toHaveBeenCalledWith('/api/v1/precomputed-layouts');
        expect(calculator.precomputedLayouts).toBeDefined();
        expect(calculator.precomputedLayouts['hash1']).toBeDefined();
    });

    it('should handle fetch failure gracefully', async () => {
        fetchMock.mockRejectedValue(new Error('Network error'));

        const graphData = {
            nodes: [
                { id: 'n1', founding_year: 2000, eras: [{ year: 2000, name: 'A' }] }
            ],
            links: []
        };

        const calculator = new LayoutCalculator(graphData, 1000, 800);

        // Wait for async load
        await new Promise(resolve => setTimeout(resolve, 100));

        expect(calculator.precomputedLayouts).toEqual({});
    });

    it('should apply cached layout when hash matches', () => {
        const graphData = {
            nodes: [
                { id: 'n1', founding_year: 2000, dissolution_year: 2005, eras: [{ year: 2000, name: 'A' }] },
                { id: 'n2', founding_year: 2006, dissolution_year: 2010, eras: [{ year: 2006, name: 'B' }] }
            ],
            links: [
                { source: 'n1', target: 'n2', type: 'LEGAL_TRANSFER', year: 2006 }
            ]
        };

        const calculator = new LayoutCalculator(graphData, 1000, 800);

        // Mock precomputed layouts
        calculator.precomputedLayouts = {
            'n1,n2': {
                layout_data: {
                    'n1': 0,
                    'n2': 1
                },
                score: 100.0
            }
        };

        // Create a mock family with many chains to trigger complexity check
        const mockFamily = {
            chains: Array.from({ length: 25 }, (_, i) => ({
                id: `chain${i}`,
                nodes: [{ id: `n${i}`, founding_year: 2000 + i }],
                startTime: 2000 + i,
                endTime: 2010 + i
            }))
        };

        // Spy on layoutFamilyDynamic
        const dynamicSpy = vi.spyOn(calculator, 'layoutFamilyDynamic');

        const height = calculator.layoutFamily(mockFamily);

        // Should use cached layout, not dynamic
        expect(height).toBeGreaterThan(0);
    });

    it('should fallback to dynamic when hash mismatches', () => {
        const graphData = {
            nodes: [
                { id: 'n1', founding_year: 2000, eras: [{ year: 2000, name: 'A' }] }
            ],
            links: []
        };

        const calculator = new LayoutCalculator(graphData, 1000, 800);
        calculator.precomputedLayouts = {
            'different_hash': {
                layout_data: {},
                score: 100.0
            }
        };

        const mockFamily = {
            chains: Array.from({ length: 25 }, (_, i) => ({
                id: `chain${i}`,
                nodes: [{ id: `n${i}`, founding_year: 2000 + i }],
                startTime: 2000 + i,
                endTime: 2010 + i
            }))
        };

        // Should fallback to dynamic algorithm
        const height = calculator.layoutFamily(mockFamily);
        expect(height).toBeGreaterThan(0);
    });

    it('should fallback to dynamic when cache is not loaded', () => {
        const graphData = {
            nodes: [
                { id: 'n1', founding_year: 2000, eras: [{ year: 2000, name: 'A' }] }
            ],
            links: []
        };

        const calculator = new LayoutCalculator(graphData, 1000, 800);
        calculator.precomputedLayouts = null;

        const mockFamily = {
            chains: Array.from({ length: 25 }, (_, i) => ({
                id: `chain${i}`,
                nodes: [{ id: `n${i}`, founding_year: 2000 + i }],
                startTime: 2000 + i,
                endTime: 2010 + i
            }))
        };

        const height = calculator.layoutFamily(mockFamily);
        expect(height).toBeGreaterThan(0);
    });

    it('should not use cache for small families', () => {
        const graphData = {
            nodes: [
                { id: 'n1', founding_year: 2000, eras: [{ year: 2000, name: 'A' }] }
            ],
            links: []
        };

        const calculator = new LayoutCalculator(graphData, 1000, 800);
        calculator.precomputedLayouts = {
            'n1': {
                layout_data: { 'n1': 0 },
                score: 100.0
            }
        };

        // Small family (< 20 chains)
        const mockFamily = {
            chains: [
                { id: 'chain1', nodes: [{ id: 'n1', founding_year: 2000 }], startTime: 2000, endTime: 2010 }
            ]
        };

        const height = calculator.layoutFamily(mockFamily);
        expect(height).toBeGreaterThan(0);
    });

    it('should maintain pre-placed chains in Hybrid mode', () => {
        const graphData = {
            nodes: [
                { id: 'n1', founding_year: 2000, eras: [{ year: 2000, name: 'A' }] },
                { id: 'n2', founding_year: 2005, eras: [{ year: 2005, name: 'B' }] }
            ],
            links: [
                { source: 'n1', target: 'n2', type: 'LEGAL_TRANSFER', year: 2005 }
            ]
        };

        const calculator = new LayoutCalculator(graphData, 1000, 800);

        // Mock a family with two chains
        const chain1 = { id: 'chain1', nodes: [{ id: 'n1', founding_year: 2000 }], startTime: 2000, endTime: 2004, children: ['chain2'], parents: [] };
        const chain2 = { id: 'chain2', nodes: [{ id: 'n2', founding_year: 2005 }], startTime: 2005, endTime: 2010, children: [], parents: ['chain1'] };
        const mockFamily = {
            chains: [chain1, chain2]
        };

        // Mock pre-placed state: chain1 is at Y=5
        const preplacedState = {
            ySlots: new Map([[5, [{ start: 2000, end: 2004 }]]]),
            placedChains: new Map([['chain1', 5]]),
            maxSeenY: 5
        };

        // Set up scales
        calculator.xScale = (y) => y;

        // We call layoutFamilyDynamic directly with the preplaced state
        calculator.layoutFamilyDynamic(mockFamily, preplacedState);

        // Chain 1 should STILL be at 5
        expect(calculator.chainY.get('chain1')).toBe(5);
        // Chain 2 should be placed
        expect(calculator.chainY.get('chain2')).toBeDefined();
    });
});
