
import { LAYOUT_CONFIG } from '../config.js';
import { runGreedyPass } from '../simplifiers/greedyOptimizer.js';
import { runGroupwiseOptimization } from '../simplifiers/groupwiseOptimizer.js';
import { generateVerticalSegments } from '../utils/verticalSegments.js';

/**
 * Checks if a pass should be applied based on family metrics.
 */
function shouldApplyPass(familySize, linkCount, passConfig) {
    if (familySize < (passConfig.minFamilySize || 0)) return false;
    if (linkCount < (passConfig.minLinks || 0)) return false;
    return true;
}

/**
 * Executes a configured schedule of optimization passes.
 * 
 * @param {Array} family - Array of Chain PROXIES (strings?) or Objects? 
 *                         In LayoutCalculator it passes `family` which is sometimes a list of IDs. 
 *                         BUT in `_executePassSchedule` it expects `family` to be the "Context" and `chains` to be the array.
 *                         Let's align with the refactor: `family` is usually just an ID list in legacy code, 
 *                         but `chains` is the actual data.
 *                         We will pass `chains` as the primary subject.
 * 
 * @param {Array<Chain>} chains - The chains to optimize
 * @param {Map} chainParents - Map of chain IDs to parent chains
 * @param {Map} chainChildren - Map of chain IDs to child chains
 * @param {Array} unusedVs - Legacy/Not used directly here, but usually passed to optimizers? 
 *                           Actually optimizers regenerate it. We can ignore it or remove it.
 *                           Refactor: We won't accept it. We define it internally.
 * @param {Function} checkCollision - Collision detection function
 * @param {Map} ySlots - Spatial index
 * @param {Function} logScoreCallback - Callback for logging metrics (optional)
 * @param {Array} scheduleOverride - Optional schedule to override config
 */
export function executePassSchedule(
    familyIds, /* Legacy/Context */
    chains,
    chainParents,
    chainChildren,
    unusedVs, /* Kept for signature compatibility if needed, but unused */
    checkCollision,
    ySlots,
    logScoreCallback = null,
    scheduleOverride = null
) {
    const schedule = scheduleOverride || LAYOUT_CONFIG.PASS_SCHEDULE;

    // Calculate family metrics
    const familySize = chains.length || 0;
    let linkCount = 0;
    chains.forEach(c => {
        linkCount += (chainParents.get(c.id)?.length || 0);
        linkCount += (chainChildren.get(c.id)?.length || 0);
    });
    linkCount = linkCount / 2; // undirected edges

    let globalPassIndex = 0;

    for (const pass of schedule) {
        if (!shouldApplyPass(familySize, linkCount, pass)) continue;

        for (let i = 0; i < pass.iterations; i++) {
            for (const strategy of pass.strategies) {
                // Rebuild vertical segments for accurate blocker calculation
                const verticalSegments = generateVerticalSegments(chains, chainParents);

                if (strategy === 'HYBRID') {
                    // Note: runGroupwiseOptimization expects (familyChains, chains, ...)
                    // Here familyChains IS chains.
                    runGroupwiseOptimization(chains, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);
                } else {
                    runGreedyPass(chains, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots, strategy);
                }

                // Log metrics
                if (logScoreCallback) {
                    logScoreCallback(globalPassIndex++, chains, chainParents, chainChildren, verticalSegments, checkCollision, ySlots);
                }
            }
        }
    }
}
