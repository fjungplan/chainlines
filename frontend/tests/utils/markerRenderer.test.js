
import { describe, it, expect, vi } from 'vitest';
import { MarkerRenderer } from '../../src/utils/markerRenderer';
import { VISUALIZATION } from '../../src/constants/visualization';
import * as d3 from 'd3';

// Mock D3 selection
const mockD3Selection = {
    selectAll: vi.fn().mockReturnThis(),
    data: vi.fn().mockReturnThis(),
    join: vi.fn().mockReturnThis(),
    attr: vi.fn().mockReturnThis(),
    style: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
    append: vi.fn().mockReturnThis(),
    select: vi.fn().mockReturnThis(),
    empty: vi.fn(),
};

// Mock D3
vi.mock('d3', () => ({
    select: vi.fn(() => mockD3Selection),
}));

describe('MarkerRenderer', () => {
    const mockG = {
        select: vi.fn().mockReturnThis(),
        append: vi.fn().mockReturnThis(),
        selectAll: vi.fn().mockReturnThis(),
        data: vi.fn().mockReturnThis(),
        join: vi.fn().mockReturnThis(),
        attr: vi.fn().mockReturnThis(),
    };

    const mockLinks = [
        {
            source: 'A',
            target: 'B',
            year: 2024,
            type: 'LEGAL_TRANSFER',
            sameSwimlane: true,
            path: null,
            targetX: 100,
            targetY: 200,
        }
    ];

    it('calculates marker dimensions based on nodeHeight', () => {
        // Setup D3 mock chain for the specific render flow
        // We need to capture the functions passed to .attr() to verify calculations

        // Simplification for the TDD phase:
        // We are testing the *calculation logic* which we will extract.
        // Let's test the helper method directly if we make it static/exported,
        // or inspect the calls.

        const layout = {
            nodeHeight: 50
        };

        // Expected values
        const expectedHeight = 50 * 0.9; // 45
        const expectedHalfHeight = expectedHeight / 2; // 22.5
        const expectedRadius = Math.max(3.5, 50 * 0.12); // 6

        // Since testing D3 side-effects is verbose, let's assume we expose a helper 
        // to get marker dimensions, which is cleaner to test.
        const dims = MarkerRenderer.getMarkerDimensions(layout);

        expect(dims.lineHeight).toBe(45);
        expect(dims.halfHeight).toBe(22.5);
        expect(dims.radius).toBe(6);
        expect(dims.strokeWidth).toBe(50 * 0.08); // 4
    });

    it('respects minimum dimensions', () => {
        const layout = {
            nodeHeight: 10 // Very small
        };

        const dims = MarkerRenderer.getMarkerDimensions(layout);

        expect(dims.radius).toBe(3.5); // Min radius
        expect(dims.strokeWidth).toBe(2); // Min stroke
    });
});
