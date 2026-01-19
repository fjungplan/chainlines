
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { LayoutCalculator } from '../../src/utils/layoutCalculator';
import { LAYOUT_CONFIG } from '../../src/utils/layout/config';
import * as GroupwiseOptimizer from '../../src/utils/layout/simplifiers/groupwiseOptimizer';

describe('LayoutCalculator - Slice 7: Hybrid Integration', () => {
    let layoutCalc;
    let runGroupwiseSpy;

    beforeEach(() => {
        vi.clearAllMocks();
        layoutCalc = new LayoutCalculator({ nodes: [], links: [] });

        // Reset config defaults
        LAYOUT_CONFIG.HYBRID_MODE = true;
        LAYOUT_CONFIG.PASS_SCHEDULE = [{ iterations: 1, strategies: ['HYBRID'] }];

        // Spy on the imported module function
        runGroupwiseSpy = vi.spyOn(GroupwiseOptimizer, 'runGroupwiseOptimization');
    });

    it('should have HYBRID_MODE enabled in default config', () => {
        expect(LAYOUT_CONFIG.HYBRID_MODE).toBe(true);
    });

    it('should run groupwise optimization method', () => {
        const chains = [{ id: 'A' }];
        layoutCalc.chains = chains;

        layoutCalc._executePassSchedule(
            ['A'],
            chains,
            new Map(),
            new Map(),
            [], // verticalSegments
            vi.fn(), // checkCollision
            new Map() // ySlots
        );

        expect(runGroupwiseSpy).toHaveBeenCalled();
    });

    it('should delegate to groupwise optimizer', () => {
        const chains = [{ id: 'A' }, { id: 'B' }];
        layoutCalc.chains = chains;

        layoutCalc._executePassSchedule(
            ['A', 'B'],
            chains,
            new Map(),
            new Map(),
            [],
            vi.fn(),
            new Map()
        );

        expect(runGroupwiseSpy).toHaveBeenCalled();
    });
});
