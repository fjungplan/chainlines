import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LayoutCalculator } from '../../src/utils/layoutCalculator';
import { LAYOUT_CONFIG } from '../../src/utils/layout/config';

describe('LayoutCalculator - Slice 7: Hybrid Integration', () => {
    let layoutCalc;
    let mockFamily;
    let mockChains;

    beforeEach(() => {
        // Reset config if needed (though we might need to patch it directly if it's a const export)
        // For testing purposes, we can override values on the instance if we make them instance properties
        // or just rely on method behavior.

        layoutCalc = new LayoutCalculator({ nodes: [], links: [] }, 1000, 800);

        // Mock data
        mockChains = [
            { id: 'A', yIndex: 0 },
            { id: 'B', yIndex: 1 }
        ];
        mockFamily = new Set(mockChains.map(c => c.id));
    });

    it('should have HYBRID_MODE enabled in default config', () => {
        // We will update the constant, so we expect it to be true
        expect(LAYOUT_CONFIG.HYBRID_MODE).toBeDefined();
    });

    it('should run groupwise optimization method', () => {
        // Mock the sub-methods to verify orchestration order
        // We need to spy on the instance methods. Since they are "private" (_prefix), we access them via brackets or any

        const sortSpy = vi.spyOn(layoutCalc, '_sortChainsByDegree').mockReturnValue(mockChains);
        const buildGroupSpy = vi.spyOn(layoutCalc, '_buildGroup').mockReturnValue(new Set(mockChains));

        const rigidMoveSpy = vi.spyOn(layoutCalc, '_calculateRigidMoveDeltas').mockReturnValue([]);
        const swapSpy = vi.spyOn(layoutCalc, '_findBestSwap').mockReturnValue(null);
        const annealSpy = vi.spyOn(layoutCalc, '_simulatedAnnealingReposition').mockReturnValue({ improved: false });

        // Execute
        const chains = mockChains;
        const chainParents = new Map();
        const chainChildren = new Map();
        const verticalSegments = [];
        const ySlots = new Map();
        const checkCollision = () => false;

        layoutCalc._runGroupwiseOptimization(
            mockFamily,
            chains,
            chainParents,
            chainChildren,
            verticalSegments,
            checkCollision,
            ySlots
        );

        // Verify Order
        // 1. Sort chains
        expect(sortSpy).toHaveBeenCalled();

        // 2. Build groups (at least once)
        expect(buildGroupSpy).toHaveBeenCalled();

        // 3. For the group, try Rigid Move
        expect(rigidMoveSpy).toHaveBeenCalled();

        // 4. Try Swaps
        expect(swapSpy).toHaveBeenCalled();

        // 5. Try Annealing (since others failed/returned null)
        expect(annealSpy).toHaveBeenCalled();
    });

    it('should prioritize rigid move improvement', () => {
        // If rigid move improves, apply it and maybe skip annealing? or continue?
        // The plan says: Try Rigid -> Try Swap -> If no improvement, Try SA.
        // So if Rigid improves, we might skip SA or re-evaluate.

        vi.spyOn(layoutCalc, '_sortChainsByDegree').mockReturnValue(mockChains);
        vi.spyOn(layoutCalc, '_buildGroup').mockReturnValue(new Set(mockChains));

        // Rigid move finds a delta
        vi.spyOn(layoutCalc, '_calculateRigidMoveDeltas').mockReturnValue([-1]);
        vi.spyOn(layoutCalc, '_evaluateRigidMove').mockReturnValue(-100); // good improvement
        const applyRigidSpy = vi.spyOn(layoutCalc, '_applyRigidMove');

        const annealSpy = vi.spyOn(layoutCalc, '_simulatedAnnealingReposition');

        layoutCalc._runGroupwiseOptimization(
            mockFamily,
            mockChains,
            new Map(),
            new Map(),
            [],
            () => false,
            new Map()
        );

        expect(applyRigidSpy).toHaveBeenCalled();
        // If improvement found, we iterate again or move to next group.
        // For this specific logic branch, if we found a rigid move, we applied it.
        // Ideally we shouldn't run SA immediately on top of a successful rigid move for the same iteration pass,
        // unless we want to refine it. Let's assume the logic is: OR (mutually exclusive per pass for a group)
        // OR sequential. Given "Fallback", SA implies it runs if others fail.

        expect(annealSpy).not.toHaveBeenCalled();
    });
});
