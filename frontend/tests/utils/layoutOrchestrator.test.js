import { describe, it, expect, beforeEach, vi } from 'vitest';
import { LayoutCalculator, LAYOUT_CONFIG } from '../../src/utils/layoutCalculator';

describe('LayoutCalculator - Slice 8A: Configurable Pass Orchestrator', () => {
    let layoutCalc;
    let mockFamily;
    let mockChains;
    let mockParents;
    let mockChildren;

    beforeEach(() => {
        layoutCalc = new LayoutCalculator({ nodes: [], links: [] }, 1000, 800);

        // Mock internal optimization methods
        layoutCalc._runOptimizationPass = vi.fn(); // Mock the generic pass runner
        layoutCalc._runGroupwiseOptimization = vi.fn(); // Mock hybrid pass

        // Mock data structures
        mockChains = [
            { id: 'A', startTime: 2000, nodes: [{ id: 'A' }] },
            { id: 'B', startTime: 2005, nodes: [{ id: 'B' }] }
        ];
        mockFamily = new Set(mockChains);
        mockParents = new Map();
        mockChildren = new Map();
    });

    it('should execute strategies in defined order and iterations', () => {
        // Custom schedule for test
        const testSchedule = [
            { strategies: ['PARENTS'], iterations: 3, minFamilySize: 0, minLinks: 0 },
            { strategies: ['CHILDREN'], iterations: 2, minFamilySize: 0, minLinks: 0 }
        ];

        // Initialize Spy to track execution order
        // We assume the implementation will call _runOptimizationPass(strategy)

        // Mock config injection (assuming we can override or pass it)
        // Since LAYOUT_CONFIG is imported, we might need to mock the module or 
        // design the method to accept a config override. 
        // For now, let's assume we can pass the schedule to the specific method or mock config.
        // Actually, `layoutFamily` usually reads global config. 
        // Let's modify the instance's config if possible or assume dependency injection.

        // Workaround: We'll modify the loop to accept an optional schedule argument for testing
        // or we just mock the config property on the class execution context if strictly bound.

        layoutCalc._executePassSchedule(mockFamily, mockChains, mockParents, mockChildren, [], () => { }, new Map(), testSchedule);

        expect(layoutCalc._runOptimizationPass).toHaveBeenCalledTimes(5);
        expect(layoutCalc._runOptimizationPass).toHaveBeenNthCalledWith(1, expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), 'PARENTS');
        expect(layoutCalc._runOptimizationPass).toHaveBeenNthCalledWith(3, expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), 'PARENTS');
        expect(layoutCalc._runOptimizationPass).toHaveBeenNthCalledWith(4, expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), 'CHILDREN');
        expect(layoutCalc._runOptimizationPass).toHaveBeenNthCalledWith(5, expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), 'CHILDREN');
    });

    it('should support multiple strategies per pass entry (Alternating)', () => {
        const testSchedule = [
            { strategies: ['PARENTS', 'CHILDREN'], iterations: 2, minFamilySize: 0, minLinks: 0 }
        ];
        // Should run: PARENTS, CHILDREN, PARENTS, CHILDREN

        layoutCalc._executePassSchedule(mockFamily, mockChains, mockParents, mockChildren, [], () => { }, new Map(), testSchedule);

        expect(layoutCalc._runOptimizationPass).toHaveBeenCalledTimes(4);
        expect(layoutCalc._runOptimizationPass).toHaveBeenNthCalledWith(1, expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), 'PARENTS');
        expect(layoutCalc._runOptimizationPass).toHaveBeenNthCalledWith(2, expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), 'CHILDREN');
        expect(layoutCalc._runOptimizationPass).toHaveBeenNthCalledWith(3, expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), 'PARENTS');
        expect(layoutCalc._runOptimizationPass).toHaveBeenNthCalledWith(4, expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), expect.anything(), 'CHILDREN');
    });

    it('should skip passes if family size is below threshold', () => {
        // Helper to calculate size: mockFamily.size is 2.
        const testSchedule = [
            { strategies: ['HUBS'], iterations: 1, minFamilySize: 10, minLinks: 0 } // Threshold 10, actual 2 -> Skip
        ];

        layoutCalc._executePassSchedule(mockFamily, mockChains, mockParents, mockChildren, [], () => { }, new Map(), testSchedule);

        expect(layoutCalc._runOptimizationPass).not.toHaveBeenCalled();
    });

    it('should skip passes if family links are below threshold', () => {
        // Calculate links: sum of parents + children size / 2 (undirected) or similar metric.
        // For test, let's assume implementation uses a helper we can deduce behavior from.
        // Let's assume total edges count.

        const testSchedule = [
            { strategies: ['HUBS'], iterations: 1, minFamilySize: 0, minLinks: 5 }
        ];

        // Our mock setup has no links (empty maps)
        layoutCalc._executePassSchedule(mockFamily, mockChains, mockParents, mockChildren, [], () => { }, new Map(), testSchedule);

        expect(layoutCalc._runOptimizationPass).not.toHaveBeenCalled();
    });

    it('should properly delegate HYBRID strategy to _runGroupwiseOptimization', () => {
        const testSchedule = [
            { strategies: ['HYBRID'], iterations: 1, minFamilySize: 0, minLinks: 0 }
        ];

        layoutCalc._executePassSchedule(mockFamily, mockChains, mockParents, mockChildren, [], () => { }, new Map(), testSchedule);

        expect(layoutCalc._runGroupwiseOptimization).toHaveBeenCalledTimes(1);
    });
});
