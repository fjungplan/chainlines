
import { describe, it, expect } from 'vitest';
import { getSortedTimelineItems } from '../../src/utils/teamHistoryUtils';

describe('getSortedTimelineItems', () => {
    it('sorts eras descending by year', () => {
        const timeline = [
            { year: 2000, name: 'Team 2000' },
            { year: 2002, name: 'Team 2002' },
            { year: 2001, name: 'Team 2001' }
        ];
        // Empty events logic
        const sorted = getSortedTimelineItems(timeline, []);
        expect(sorted).toHaveLength(3);
        expect(sorted[0].year).toBe(2002);
        expect(sorted[1].year).toBe(2001);
        expect(sorted[2].year).toBe(2000);
    });

    it('interleaves events correctly (sorting by year)', () => {
        const timeline = [
            { year: 2000, name: 'Era 2000' },
            { year: 2002, name: 'Era 2002' }
        ];
        const events = [
            { year: 2001, event_type: 'MERGE' }
        ];

        const sorted = getSortedTimelineItems(timeline, events);
        expect(sorted).toHaveLength(3);
        expect(sorted[0].year).toBe(2002);
        expect(sorted[1].year).toBe(2001); // Event
        expect(sorted[1].type).toBe('EVENT');
        expect(sorted[2].year).toBe(2000);
    });

    it('places events "above" eras in the same year', () => {
        const timeline = [
            { year: 2000, name: 'Era 2000' }
        ];
        const events = [
            { year: 2000, event_type: 'SPLIT' }
        ];

        const sorted = getSortedTimelineItems(timeline, events);
        expect(sorted).toHaveLength(2);

        // User requested: Era should be "above" (index 0) lineage event of same year
        expect(sorted[0].type).toBe('ERA');
        expect(sorted[1].type).toBe('EVENT');
    });

    it('handles null/empty inputs gracefully', () => {
        expect(getSortedTimelineItems(null, [])).toEqual([]);
        expect(getSortedTimelineItems([], null)).toEqual([]);
    });
});
