import { describe, it, expect } from 'vitest';
import { calculateSingleChainCost, getAffectedChains, calculateCostDelta } from '../../../src/utils/layout/utils/costCalculator';
import LAYOUT_CONFIG from '../../../src/utils/layout/layout_config.json';

describe('costCalculator', () => {
    describe('calculateSingleChainCost', () => {
        // Helper to generic chain objects
        const createChain = (id, yIndex = 0, startTime = 2000, endTime = 2010) => ({
            id, yIndex, startTime, endTime
        });

        it('should return 0 cost for isolated chain', () => {
            const chain = createChain('c1');
            const chainParents = new Map();
            const chainChildren = new Map();
            const verticalSegments = [];
            const checkCollision = () => false;

            const cost = calculateSingleChainCost(
                chain,
                0,
                chainParents,
                chainChildren,
                verticalSegments,
                checkCollision
            );

            expect(cost).toBe(0);
        });

        it('should calculate attraction cost to parents', () => {
            // Parent at y=0, we place child at y=10
            const parent = createChain('p1', 0);
            const chain = createChain('c1');
            const chainParents = new Map([['c1', [parent]]]);
            const chainChildren = new Map();
            const verticalSegments = [];
            const checkCollision = () => false;

            const cost = calculateSingleChainCost(
                chain,
                10,
                chainParents,
                chainChildren,
                verticalSegments,
                checkCollision
            );

            // dist = 10. Cost = 10^2 * weight
            const expectedCost = (100) * LAYOUT_CONFIG.WEIGHTS.ATTRACTION;
            expect(cost).toBe(expectedCost);
        });

        it('should calculate attraction cost to children', () => {
            // Child at y=10, we place parent at y=0
            const child = createChain('child1', 10);
            const chain = createChain('p1');
            const chainParents = new Map(); // p1 has no parents
            const chainChildren = new Map([['p1', [child]]]);
            const verticalSegments = [];
            const checkCollision = () => false;

            const cost = calculateSingleChainCost(
                chain,
                0,
                chainParents,
                chainChildren,
                verticalSegments,
                checkCollision
            );

            // dist = 10. Cost = 10^2 * weight
            const expectedCost = (100) * LAYOUT_CONFIG.WEIGHTS.ATTRACTION;
            expect(cost).toBe(expectedCost);
        });

        it('should calculate cut-through cost', () => {
            // Parent at y=0, placing child at y=5
            // Collision at y=2
            const parent = createChain('p1', 0);
            const chain = createChain('c1');
            const chainParents = new Map([['c1', [parent]]]);
            const chainChildren = new Map();
            const verticalSegments = [];

            // Mock collision check: returns true for lane 2
            const checkCollision = (lane) => lane === 2;

            const cost = calculateSingleChainCost(
                chain,
                5,
                chainParents,
                chainChildren,
                verticalSegments,
                checkCollision
            );

            // Attraction: 5^2 * ATTRACTION
            // Cut-through: 1 collision * CUT_THROUGH
            const expectedAttraction = 25 * LAYOUT_CONFIG.WEIGHTS.ATTRACTION;
            const expectedCutThrough = LAYOUT_CONFIG.WEIGHTS.CUT_THROUGH;

            expect(cost).toBe(expectedAttraction + expectedCutThrough);
        });

        it('should calculate blocker cost', () => {
            // Placing chain at y=5
            const chain = createChain('c1', 0, 2000, 2010);
            const chainParents = new Map();
            const chainChildren = new Map();
            // Vertical segment from y=0 to y=10 that blocks (time covers chain start)
            const verticalSegments = [{
                y1: 0,
                y2: 10,
                time: 2005,
                childId: 'other1',
                parentId: 'other2'
            }];
            const checkCollision = () => false;

            const cost = calculateSingleChainCost(
                chain,
                5,
                chainParents,
                chainChildren,
                verticalSegments,
                checkCollision
            );

            // Blocker weight applis
            expect(cost).toBe(LAYOUT_CONFIG.WEIGHTS.BLOCKER);
        });

        it('should ignore blockers that are its own segments', () => {
            const chain = createChain('c1', 0, 2000, 2010);
            const verticalSegments = [{
                y1: 0,
                y2: 10,
                time: 2005,
                childId: 'c1', // It's my own child link
                parentId: 'p1'
            }];
            const checkCollision = () => false;

            const cost = calculateSingleChainCost(
                chain,
                5,
                new Map(),
                new Map(),
                verticalSegments,
                checkCollision
            );

            expect(cost).toBe(0);
        });

        it('should calculate Y-shape cost for splits', () => {
            // Chain is parent of c1 and c2.
            // We place Chain at y=5.
            // c1 is at y=4 (close, diff=1)
            // c2 is at y=8 (far, diff=3)
            // Y-Shape penalty applies if sibling distance from placement is < 2? 
            // Wait, let's re-read the logic.

            // Original logic:
            // children.forEach(c => {
            //   spouses = chainParents.get(c.id)
            //   spouses.forEach(spouse => {
            //      if (spouse !== chain) ...
            //      if (Math.abs(spouse.yIndex - y) < 2) cost += Y_SHAPE
            //   })
            // })
            // This logic checks if ANY OTHER PARENT of my child is too close to me.
            // i.e., merging parents shouldn't be squeezed together? 

            // Scenario: Merge
            // Child c1 has parents p1 (me) and p2 (spouse).
            // Placing p1 at y=5.
            // p2 is at y=5 (diff=0).
            // Should apply penalty.

            const me = createChain('me');
            const spouse = createChain('spouse', 5);
            const child = createChain('child'); // y doesn't matter for this check specifically?

            const chainChildren = new Map([['me', [child]]]);
            // Child's parents are me and spouse
            const chainParents = new Map([['child', [me, spouse]]]);

            // Let's verify ONLY Y-shape contribution.
            // If child is at y=5, attraction is 0.
            child.yIndex = 5;

            const cost = calculateSingleChainCost(
                me,
                5, // Placing me at same Y as spouse
                chainParents,
                chainChildren,
                [],
                () => false
            );

            expect(cost).toBe(LAYOUT_CONFIG.WEIGHTS.Y_SHAPE);
        });
    });

    describe('getAffectedChains', () => {
        // Helper to generic chain objects
        const createChain = (id, startTime = 2000, endTime = 2010) => ({
            id, startTime, endTime
        });

        it('should include direct parents and children', () => {
            const moved = createChain('moved');
            const parent = createChain('parent');
            const child = createChain('child');
            // Unrelated needs to be temporally distinct to result in false
            const unrelated = createChain('unrelated', 3000, 3010);

            const chains = [moved, parent, child, unrelated];
            const chainParents = new Map([['moved', [parent]]]);
            const chainChildren = new Map([['moved', [child]]]);

            const affected = getAffectedChains(moved, 0, 1, chains, chainParents, chainChildren, []);

            expect(affected.has('parent')).toBe(true);
            expect(affected.has('child')).toBe(true);
            expect(affected.has('unrelated')).toBe(false);
        });

        it('should include temporally overlapping chains (potential blockers)', () => {
            const moved = createChain('moved', 2000, 2010);
            const overlapping = createChain('overlap', 2005, 2015);
            const nonOverlapping = createChain('clean', 2020, 2030);

            const chains = [moved, overlapping, nonOverlapping];
            const chainParents = new Map();
            const chainChildren = new Map();

            const affected = getAffectedChains(moved, 0, 1, chains, chainParents, chainChildren, []);

            expect(affected.has('overlap')).toBe(true);
            expect(affected.has('clean')).toBe(false);
        });
    });

    describe('calculateCostDelta', () => {
        const createChain = (id, yIndex, startTime = 2000, endTime = 2010) => ({
            id, yIndex, startTime, endTime
        });

        it('should calculate cost difference and revert state', () => {
            // Setup simple scenario:
            // Chain at y=0. Want to move to y=10.
            // Parent at y=10.
            // Old Cost: dist(0, 10)^2 = 100 * Weight
            // New Cost: dist(10, 10)^2 = 0
            // Delta should be negative (improvement).

            const chain = createChain('c1', 0);
            const parent = createChain('p1', 10);

            const chains = [chain, parent];
            const chainParents = new Map([['c1', [parent]]]);
            const chainChildren = new Map();
            const verticalSegments = [];
            const checkCollision = () => false;

            const ySlots = new Map();
            ySlots.set(0, [{ start: 2000, end: 2010, chainId: 'c1' }]);

            // Mock affected chains (parent is affected)
            const affected = new Set(['p1']);

            const delta = calculateCostDelta(
                chain,
                0, // oldY
                10, // newY
                affected,
                chains,
                chainParents,
                chainChildren,
                verticalSegments,
                checkCollision,
                ySlots
            );

            // Expect negative delta (cost reduction)
            expect(delta).toBeLessThan(0);

            // Verify state reversion
            expect(chain.yIndex).toBe(0); // Should be back at 0
            const newSlotContent = ySlots.get(10) || [];
            expect(newSlotContent).toHaveLength(0); // New slot should be clean (or empty)
            expect(ySlots.get(0)).toHaveLength(1); // Old slot restored
        });
    });
});
