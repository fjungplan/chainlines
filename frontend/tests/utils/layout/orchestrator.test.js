
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { executePassSchedule } from '../../../src/utils/layout/orchestrator/layoutOrchestrator';
import { LAYOUT_CONFIG } from '../../../src/utils/layout/config';
import * as GreedyOptimizer from '../../../src/utils/layout/simplifiers/greedyOptimizer';
import * as GroupwiseOptimizer from '../../../src/utils/layout/simplifiers/groupwiseOptimizer';
import * as VerticalSegments from '../../../src/utils/layout/utils/verticalSegments';

// Mock dependencies
vi.mock('../../../src/utils/layout/simplifiers/greedyOptimizer', () => ({
    runGreedyPass: vi.fn(),
}));

vi.mock('../../../src/utils/layout/simplifiers/groupwiseOptimizer', () => ({
    runGroupwiseOptimization: vi.fn(),
}));

vi.mock('../../../src/utils/layout/utils/verticalSegments', () => ({
    generateVerticalSegments: vi.fn().mockReturnValue([]),
}));

describe('LayoutOrchestrator', () => {
    let chains, chainParents, chainChildren, checkCollision, ySlots, logScoreStub;

    beforeEach(() => {
        vi.clearAllMocks();

        // Mock Data
        chains = [{ id: 'A' }, { id: 'B' }];
        chainParents = new Map([['A', []], ['B', []]]);
        chainChildren = new Map([['A', []], ['B', []]]);
        checkCollision = vi.fn();
        ySlots = new Map();
        logScoreStub = vi.fn();

        // Default Config
        LAYOUT_CONFIG.PASS_SCHEDULE = [
            { iterations: 1, strategies: ['greedy-strategy'] }
        ];
    });

    it('should run not run if family is too small', () => {
        const filters = { minFamilySize: 5 };
        const passConfig = { ...LAYOUT_CONFIG.PASS_SCHEDULE[0], ...filters };
        const schedule = [passConfig];

        executePassSchedule(
            chains, chains, chainParents, chainChildren, [], checkCollision, ySlots, logScoreStub, schedule
        );

        expect(GreedyOptimizer.runGreedyPass).not.toHaveBeenCalled();
        expect(GroupwiseOptimizer.runGroupwiseOptimization).not.toHaveBeenCalled();
    });

    it('should run greedy pass when configured', () => {
        const schedule = [{ iterations: 1, strategies: ['A'] }];

        executePassSchedule(
            chains, chains, chainParents, chainChildren, [], checkCollision, ySlots, logScoreStub, schedule
        );

        expect(GreedyOptimizer.runGreedyPass).toHaveBeenCalledWith(
            chains, chains, chainParents, chainChildren, expect.anything(), checkCollision, ySlots, 'A'
        );
    });

    it('should run groupwise optimization when configured', () => {
        const schedule = [{ iterations: 1, strategies: ['HYBRID'] }];

        executePassSchedule(
            chains, chains, chainParents, chainChildren, [], checkCollision, ySlots, logScoreStub, schedule
        );

        expect(GroupwiseOptimizer.runGroupwiseOptimization).toHaveBeenCalledWith(
            chains, chains, chainParents, chainChildren, expect.anything(), checkCollision, ySlots
        );
    });

    it('should regenerate vertical segments between strategies', () => {
        const schedule = [{ iterations: 1, strategies: ['A', 'B'] }];

        executePassSchedule(
            chains, chains, chainParents, chainChildren, [], checkCollision, ySlots, logScoreStub, schedule
        );

        // 2 strategies * 1 iteration = 2 regenerations
        // Plus maybe initial one? The implementation needs to ensure segments are fresh.
        // Based on existing logic, it generates inside the loop.
        expect(VerticalSegments.generateVerticalSegments).toHaveBeenCalledTimes(2);
    });

    it('should call logScore callback', () => {
        const schedule = [{ iterations: 1, strategies: ['A'] }];

        executePassSchedule(
            chains, chains, chainParents, chainChildren, [], checkCollision, ySlots, logScoreStub, schedule
        );

        expect(logScoreStub).toHaveBeenCalled();
    });
});
