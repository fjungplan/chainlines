
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Scoreboard } from '../../src/utils/layout/analytics/layoutScoreboard';
import { LAYOUT_CONFIG } from '../../src/utils/layout/config';
import * as CostCalculator from '../../src/utils/layout/utils/costCalculator';

// Mock CostCalculator
vi.mock('../../src/utils/layout/utils/costCalculator', () => ({
    calculateSingleChainCost: vi.fn().mockReturnValue(10)
}));

describe('Scoreboard (Slice R10)', () => {
    let scoreboard;
    let chains;
    let configBackup;

    beforeEach(() => {
        configBackup = JSON.parse(JSON.stringify(LAYOUT_CONFIG));
        scoreboard = new Scoreboard();

        // Mock Data
        chains = [
            { id: 'c1', yIndex: 0 },
            { id: 'c2', yIndex: 0 }
        ];
    });

    afterEach(() => {
        Object.assign(LAYOUT_CONFIG, configBackup);
        vi.clearAllMocks();
    });

    it('should calculate metrics correctly', () => {
        const metrics = scoreboard.calculateScore(
            chains, new Map(), new Map(), [], () => false, new Map()
        );

        expect(metrics).toHaveProperty('totalCost', 20); // 2 chains * 10 cost
        expect(metrics).toHaveProperty('crossings');
        expect(metrics).toHaveProperty('vacantLanes');
    });

    it('should not log scores if disabled in config', () => {
        LAYOUT_CONFIG.SCOREBOARD = { ENABLED: false };
        const logSpy = vi.fn();
        LAYOUT_CONFIG.SCOREBOARD.LOG_FUNCTION = logSpy;

        scoreboard.logScore(0, chains, new Map(), new Map(), [], () => false, new Map());

        expect(logSpy).not.toHaveBeenCalled();
        expect(scoreboard.scoreHistory).toHaveLength(0);
    });

    it('should log scores via LOG_FUNCTION if enabled', () => {
        LAYOUT_CONFIG.SCOREBOARD = {
            ENABLED: true,
            LOG_FUNCTION: vi.fn()
        };

        scoreboard.logScore(1, chains, new Map(), new Map(), [], () => false, new Map());

        expect(LAYOUT_CONFIG.SCOREBOARD.LOG_FUNCTION).toHaveBeenCalledWith(1, expect.objectContaining({
            totalCost: 20
        }));
        expect(scoreboard.scoreHistory).toHaveLength(1);
        expect(scoreboard.scoreHistory[0].pass).toBe(1);
        expect(scoreboard.scoreHistory[0].totalCost).toBe(20);
    });

    it('should handle invalid input gracefully', () => {
        LAYOUT_CONFIG.SCOREBOARD = { ENABLED: true };
        const notArray = {};

        scoreboard.logScore(1, notArray, new Map(), new Map(), [], () => false, new Map());

        // Should not crash, cost 0
        expect(scoreboard.scoreHistory[0].totalCost).toBe(0);
    });
});
