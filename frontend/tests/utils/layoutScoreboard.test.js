
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { LayoutCalculator, LAYOUT_CONFIG } from '../../src/utils/layoutCalculator';

describe('Layout Scoreboard (Slice 8B)', () => {
    let layoutCalculator;
    let family;
    let configBackup;

    beforeEach(() => {
        configBackup = JSON.parse(JSON.stringify(LAYOUT_CONFIG));
        layoutCalculator = new LayoutCalculator({ nodes: [], links: [] }, 1000, 800);

        // Mock Family Setup
        family = new Set();
        const chains = [
            { id: 'c1', startTime: 1900, endTime: 1910, yIndex: 0, nodes: [] },
            { id: 'c2', startTime: 1905, endTime: 1915, yIndex: 0, nodes: [] },
            { id: 'c3', startTime: 1920, endTime: 1930, yIndex: 1, nodes: [] }
        ];
        chains.forEach(c => family.add(c));
        layoutCalculator.chains = chains;
    });

    afterEach(() => {
        Object.assign(LAYOUT_CONFIG, configBackup);
        vi.clearAllMocks();
    });

    it('should calculate Crossings metric correctly', () => {
        const score = layoutCalculator._calculateScore(family, new Map(), new Map(), [], () => false, new Map());
        expect(score).toHaveProperty('crossings');
        expect(score).toHaveProperty('vacantLanes');
    });

    it('should not log scores if disabled in config', () => {
        LAYOUT_CONFIG.SCOREBOARD = { ENABLED: false };
        const logSpy = vi.fn();
        LAYOUT_CONFIG.SCOREBOARD.LOG_FUNCTION = logSpy;

        // Pass dummy arguments
        layoutCalculator._logScore(0, new Set(), [], new Map(), new Map(), [], () => false, new Map());

        expect(logSpy).not.toHaveBeenCalled();
    });

    it('should log scores via LOG_FUNCTION if enabled', () => {
        LAYOUT_CONFIG.SCOREBOARD = {
            ENABLED: true,
            LOG_FUNCTION: vi.fn()
        };

        const metrics = { crossings: 5, totalCost: 100 };
        vi.spyOn(layoutCalculator, '_calculateScore').mockReturnValue(metrics);

        layoutCalculator._logScore(1, family, [], new Map(), new Map(), [], () => false, new Map());

        expect(LAYOUT_CONFIG.SCOREBOARD.LOG_FUNCTION).toHaveBeenCalledWith(1, metrics);
    });
});
