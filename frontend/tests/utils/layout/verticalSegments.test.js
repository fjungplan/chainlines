import { describe, it, expect } from 'vitest';
import { generateVerticalSegments } from '../../../src/utils/layout/utils/verticalSegments';

describe('verticalSegments', () => {
    describe('generateVerticalSegments', () => {
        it('should return empty array for empty chains', () => {
            const chains = [];
            const chainParents = new Map();

            const result = generateVerticalSegments(chains, chainParents);
            expect(result).toEqual([]);
        });

        it('should return empty array when no connections exist', () => {
            const chains = [
                { id: 'c1', yIndex: 0, startTime: 2000 },
                { id: 'c2', yIndex: 2, startTime: 2000 }
            ];
            const chainParents = new Map();

            const result = generateVerticalSegments(chains, chainParents);
            expect(result).toEqual([]);
        });

        it('should NOT generate segment for adjacent connections (diff <= 1)', () => {
            const chains = [
                { id: 'parent', yIndex: 0 },
                { id: 'child', yIndex: 1, startTime: 2005 }
            ];
            const chainParents = new Map();
            chainParents.set('child', [{ id: 'parent', yIndex: 0 }]);

            const result = generateVerticalSegments(chains, chainParents);
            expect(result).toEqual([]);
        });

        it('should generate segment for distant connections (diff > 1)', () => {
            const chains = [
                { id: 'parent', yIndex: 0 },
                { id: 'child', yIndex: 3, startTime: 2005 }
            ];
            const chainParents = new Map();
            chainParents.set('child', [{ id: 'parent', yIndex: 0 }]);

            const result = generateVerticalSegments(chains, chainParents);

            expect(result).toHaveLength(1);
            expect(result[0]).toEqual({
                y1: 0,
                y2: 3,
                time: 2005,
                childId: 'child',
                parentId: 'parent'
            });
        });

        it('should handle inverted y-indices (parent below child)', () => {
            const chains = [
                { id: 'parent', yIndex: 5 },
                { id: 'child', yIndex: 2, startTime: 2010 }
            ];
            const chainParents = new Map();
            chainParents.set('child', [{ id: 'parent', yIndex: 5 }]);

            const result = generateVerticalSegments(chains, chainParents);

            expect(result).toHaveLength(1);
            expect(result[0]).toEqual({
                y1: 2,   // min
                y2: 5,   // max
                time: 2010,
                childId: 'child',
                parentId: 'parent'
            });
        });

        it('should handle multiple parents for one child', () => {
            const chains = [
                { id: 'p1', yIndex: 0 },
                { id: 'p2', yIndex: 6 },
                { id: 'child', yIndex: 3, startTime: 2015 }
            ];
            const chainParents = new Map();
            chainParents.set('child', [
                { id: 'p1', yIndex: 0 },
                { id: 'p2', yIndex: 6 }
            ]);

            const result = generateVerticalSegments(chains, chainParents);

            expect(result).toHaveLength(2);
            // Sort to make testing reliable
            result.sort((a, b) => a.y1 - b.y1);

            expect(result[0]).toMatchObject({
                y1: 0, y2: 3, parentId: 'p1'
            });
            expect(result[1]).toMatchObject({
                y1: 3, y2: 6, parentId: 'p2'
            });
        });
    });
});
