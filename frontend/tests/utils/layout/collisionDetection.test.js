import { describe, it, expect } from 'vitest';
import { checkCollision } from '../../../src/utils/layout/utils/collisionDetection';

describe('collisionDetection', () => {
    describe('checkCollision', () => {
        it('should allow family members to touch (no gap required)', () => {
            const ySlots = new Map();
            ySlots.set(5, [
                { start: 2000, end: 2005, chainId: 'parent-chain' }
            ]);

            const family = {
                chains: [
                    { id: 'parent-chain' },
                    { id: 'child-chain' }
                ]
            };

            const chainParents = new Map();
            chainParents.set('child-chain', [{ id: 'parent-chain' }]);

            const chainChildren = new Map();
            chainChildren.set('parent-chain', [{ id: 'child-chain' }]);

            const movingChain = { id: 'child-chain' };

            // Child starts immediately after parent (2006-2010)
            // Family allows this (touching). Strangers would require a gap (start 2007).
            const result = checkCollision(
                5,
                2006,
                2010,
                null,
                movingChain,
                ySlots,
                family,
                chainParents,
                chainChildren
            );

            expect(result).toBe(false); // No collision for family (touching allowed)
        });

        it('should require 1-year gap for strangers', () => {
            const ySlots = new Map();
            ySlots.set(5, [
                { start: 2000, end: 2010, chainId: 'stranger-chain' }
            ]);

            const family = {
                chains: [
                    { id: 'stranger-chain' },
                    { id: 'moving-chain' }
                ]
            };

            const chainParents = new Map();
            chainParents.set('moving-chain', []); // No parents

            const chainChildren = new Map();
            chainChildren.set('stranger-chain', []); // Not related

            const movingChain = { id: 'moving-chain' };

            // Stranger tries to start at 2010 (no gap), should collide
            const collision1 = checkCollision(
                5,
                2010,
                2015,
                null,
                movingChain,
                ySlots,
                family,
                chainParents,
                chainChildren
            );

            expect(collision1).toBe(true); // Collision - no gap

            // Stranger starts at 2011 (adjacent/touching), should COLLIDE (visual gap enforce)
            const collision2 = checkCollision(
                5,
                2011,
                2015,
                null,
                movingChain,
                ySlots,
                family,
                chainParents,
                chainChildren
            );

            expect(collision2).toBe(true); // Touching is collision for strangers

            // Stranger starts at 2012 (1-year empty gap), should be OK
            const collision3 = checkCollision(
                5,
                2012,
                2015,
                null,
                movingChain,
                ySlots,
                family,
                chainParents,
                chainChildren
            );

            expect(collision3).toBe(false); // No collision - has gap
        });

        it('should exclude the moving chain from collision check', () => {
            const ySlots = new Map();
            ySlots.set(5, [
                { start: 2000, end: 2010, chainId: 'moving-chain' }
            ]);

            const family = {
                chains: [{ id: 'moving-chain' }]
            };

            const chainParents = new Map();
            const chainChildren = new Map();
            const movingChain = { id: 'moving-chain' };

            // Should not collide with itself
            const result = checkCollision(
                5,
                2000,
                2010,
                'moving-chain', // Exclude self
                movingChain,
                ySlots,
                family,
                chainParents,
                chainChildren
            );

            expect(result).toBe(false);
        });

        it('should handle empty ySlots', () => {
            const ySlots = new Map();
            const family = { chains: [] };
            const chainParents = new Map();
            const chainChildren = new Map();
            const movingChain = { id: 'test-chain' };

            const result = checkCollision(
                5,
                2000,
                2010,
                null,
                movingChain,
                ySlots,
                family,
                chainParents,
                chainChildren
            );

            expect(result).toBe(false); // No slots = no collision
        });

        it('should handle multiple slots in same lane', () => {
            const ySlots = new Map();
            ySlots.set(5, [
                { start: 2000, end: 2005, chainId: 'chain-a' },
                { start: 2010, end: 2015, chainId: 'chain-b' }
            ]);

            const family = {
                chains: [
                    { id: 'chain-a' },
                    { id: 'chain-b' },
                    { id: 'moving-chain' }
                ]
            };

            const chainParents = new Map();
            chainParents.set('moving-chain', []);

            const chainChildren = new Map();

            const movingChain = { id: 'moving-chain' };

            // Try to fit between the two strangers (2007-2008)
            const result = checkCollision(
                5,
                2007,
                2008,
                null,
                movingChain,
                ySlots,
                family,
                chainParents,
                chainChildren
            );

            expect(result).toBe(false); // Should fit in the gap
        });

        it('should detect collision with parent when overlapping as family', () => {
            const ySlots = new Map();
            ySlots.set(5, [
                { start: 2000, end: 2010, chainId: 'parent-chain' }
            ]);

            const family = {
                chains: [
                    { id: 'parent-chain' },
                    { id: 'child-chain' }
                ]
            };

            const chainParents = new Map();
            chainParents.set('child-chain', [{ id: 'parent-chain' }]);

            const chainChildren = new Map();
            chainChildren.set('parent-chain', [{ id: 'child-chain' }]);

            const movingChain = { id: 'child-chain' };

            // Family can overlap, but if they completely overlap it's still a collision
            // Testing standard collision logic for family: !(end < start || start > end)
            const result = checkCollision(
                5,
                2000,
                2010,
                null,
                movingChain,
                ySlots,
                family,
                chainParents,
                chainChildren
            );

            // Family members CAN overlap, so this should return true (collision)
            // because they occupy the same temporal space
            expect(result).toBe(true);
        });
    });
});
