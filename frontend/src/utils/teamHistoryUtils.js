
/**
 * Merges and sorts eras and events for chronological display.
 * 
 * Sort order: Descending by Year.
 * Tie-breaker: Within same year, Events appear "above" (more recent) than Eras.
 * 
 * @param {Array} eras - List of era objects
 * @param {Array} events - List of event objects
 * @returns {Array} Combined sorted list
 */
export function getSortedTimelineItems(timeline, events) {
    if (!timeline) return [];

    const eraItems = timeline.map(e => ({ ...e, type: 'ERA' }));
    const eventItems = (events || []).map(e => ({ ...e, type: 'EVENT' }));

    const combined = [...eraItems, ...eventItems];

    combined.sort((a, b) => {
        if (b.year !== a.year) {
            return b.year - a.year; // Descending
        }
        // Tie-breaker: Era vs Event?
        // User requested Era "above" Event. descending list means Era comes first (idx 0).
        if (a.type !== b.type) {
            return a.type === 'EVENT' ? 1 : -1; // Event after Era
        }
        return 0;
    });

    return combined;
}
