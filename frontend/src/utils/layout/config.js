/**
 * Configuration for the Physics Layout Engine
 * Tuned for global convergence of large blocks and tight local clustering.
 */
export const LAYOUT_CONFIG = {


    GROUPWISE: {
        MAX_RIGID_DELTA: 20,       // Max lanes to try for rigid move
        SA_MAX_ITER: 50,           // Simulated annealing iterations
        SA_INITIAL_TEMP: 100,      // Starting temperature
        SEARCH_RADIUS: 10          // Region around group for SA
    },

    SCOREBOARD: {
        ENABLED: false,             // Enable to dump layout metrics to JSON
        OUTPUT_DIR: 'logs/layout_scores'
    },

    // Slice 8A: Configurable Pass Orchestrator
    PASS_SCHEDULE: [
        // Phase 1: Rough sorting (Parents Push / Children Pull) - 30 iterations
        {
            strategies: ['PARENTS', 'CHILDREN'],
            iterations: 30,
            minFamilySize: 0,
            minLinks: 0
        },
        // Phase 2: Hub anchoring for structure - 10 iterations
        {
            strategies: ['HUBS'],
            iterations: 10,
            minFamilySize: 5,
            minLinks: 3
        },
        // Phase 3: Fine-tuning - 20 iterations
        {
            strategies: ['PARENTS', 'CHILDREN', 'HUBS'],
            iterations: 20,
            minFamilySize: 0,
            minLinks: 0
        },
        // Phase 4: Hybrid Optimization (Groupwise) - 1 pass
        {
            strategies: ['HYBRID'],
            iterations: 1,
            minFamilySize: 5,
            minLinks: 2
        }
    ],

    // Search Space
    SEARCH_RADIUS: 50,        // Look +/- 50 lanes away for a better spot (Global Vision)
    TARGET_RADIUS: 10,        // Look +/- 10 lanes around the exact parent/child center (Precision Snapping)

    // Forces & Penalties (Cost Function)
    WEIGHTS: {
        ATTRACTION: 100.0,       // Pull per lane of distance (High = tight families)
        CUT_THROUGH: 10000.0,   // Penalty for being sliced by a vertical link (Avoids crossings)
        BLOCKER: 5000.0,        // Penalty for sitting on someone else's link (Get out of the way)
        LANE_SHARING: 0.0,      // Temporarily disabled (strict collision handles strangers)
        Y_SHAPE: 150.0,         // Penalty for "Uneven" Merges/Splits (Forces Spouses/Siblings 2 lanes apart)
    }
};
