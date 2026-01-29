
import LAYOUT_CONFIG from '../layout_config.json';
import { calculateSingleChainCost } from '../utils/costCalculator.js';

/**
 * Scoreboard/Analytics module for Layout Algorithm (Slice 8B/R10)
 * Tracks performance metrics and logs them if enabled.
 */
export class Scoreboard {
    constructor() {
        this.scoreHistory = [];
    }

    /**
     * Logs the score for a specific pass.
     */
    logScore(passIndex, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots) {
        if (!LAYOUT_CONFIG.SCOREBOARD || !LAYOUT_CONFIG.SCOREBOARD.ENABLED) return;

        const metrics = this.calculateScore(chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);

        // Store internally
        this.scoreHistory.push({ pass: passIndex, ...metrics });

        // External log hook
        if (typeof LAYOUT_CONFIG.SCOREBOARD.LOG_FUNCTION === 'function') {
            LAYOUT_CONFIG.SCOREBOARD.LOG_FUNCTION(passIndex, metrics);
        }
    }

    /**
     * Calculates layout metrics (Total Cost, Crossings, etc.)
     */
    calculateScore(chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots) {
        let totalCost = 0;

        // Verify chains is an array
        if (!Array.isArray(chains)) {
            console.warn("Scoreboard: chains is not an array", chains);
            return { totalCost: 0, crossings: 0, vacantLanes: 0, familySplay: 0 };
        }

        chains.forEach(chain => {
            totalCost += calculateSingleChainCost(chain, chain.yIndex, chainParents, chainChildren, verticalSegments, checkCollision);
        });

        // Future: Implement actual crossing counting and splay metrics
        return {
            totalCost,
            crossings: 0,
            vacantLanes: ySlots ? ySlots.size : 0,
            familySplay: 0
        };
    }
}
