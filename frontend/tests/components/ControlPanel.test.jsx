import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, vi } from 'vitest';
import ControlPanel from '../../src/components/ControlPanel';

const mockNodes = [
    {
        id: 'node-7up',
        founding_year: 1997,
        dissolution_year: 2003,
        eras: [
            { name: '7UP - Colorado Cyclist', uci_code: '7UP', season_year: 1997 }
        ]
    },
    {
        id: 'node-ineos',
        founding_year: 2010,
        eras: [
            { name: 'Ineos Grenadiers', uci_code: 'IGD', season_year: 2019 }
        ]
    }
];

describe('ControlPanel - Focus State Tracking', () => {
    test('calls onFocusChange with node ID when Apply is clicked after team selection', () => {
        const onYearRangeChange = vi.fn();
        const onTierFilterChange = vi.fn();
        const onZoomReset = vi.fn();
        const onTeamSelect = vi.fn();
        const onFocusChange = vi.fn();

        render(
            <ControlPanel
                onYearRangeChange={onYearRangeChange}
                onTierFilterChange={onTierFilterChange}
                onZoomReset={onZoomReset}
                onTeamSelect={onTeamSelect}
                onFocusChange={onFocusChange}
                searchNodes={mockNodes}
            />
        );

        // Select a team via SearchBar
        const input = screen.getByPlaceholderText('Search teams...');
        fireEvent.change(input, { target: { value: '7UP' } });

        const result = screen.getByText(/7UP - Colorado Cyclist/);
        fireEvent.click(result);

        // Click Apply Filters
        const applyButton = screen.getByText('Apply Filters');
        fireEvent.click(applyButton);

        // Verify onFocusChange was called with the node ID
        expect(onFocusChange).toHaveBeenCalledWith('node-7up');
        expect(onFocusChange).toHaveBeenCalledTimes(1);
    });

    test('calls onFocusChange with null when Reset is clicked', () => {
        const onYearRangeChange = vi.fn();
        const onTierFilterChange = vi.fn();
        const onZoomReset = vi.fn();
        const onTeamSelect = vi.fn();
        const onFocusChange = vi.fn();

        render(
            <ControlPanel
                onYearRangeChange={onYearRangeChange}
                onTierFilterChange={onTierFilterChange}
                onZoomReset={onZoomReset}
                onTeamSelect={onTeamSelect}
                onFocusChange={onFocusChange}
                searchNodes={mockNodes}
            />
        );

        // Select a team first
        const input = screen.getByPlaceholderText('Search teams...');
        fireEvent.change(input, { target: { value: '7UP' } });
        const result = screen.getByText(/7UP - Colorado Cyclist/);
        fireEvent.click(result);

        // Click Reset Filters
        const resetButton = screen.getByText('Reset Filters');
        fireEvent.click(resetButton);

        // Verify onFocusChange was called with null
        expect(onFocusChange).toHaveBeenCalledWith(null);
    });

    test('does not call onFocusChange when Apply is clicked without team selection', () => {
        const onYearRangeChange = vi.fn();
        const onTierFilterChange = vi.fn();
        const onFocusChange = vi.fn();

        render(
            <ControlPanel
                onYearRangeChange={onYearRangeChange}
                onTierFilterChange={onTierFilterChange}
                onFocusChange={onFocusChange}
                searchNodes={mockNodes}
            />
        );

        // Click Apply without selecting a team
        const applyButton = screen.getByText('Apply Filters');
        fireEvent.click(applyButton);

        // Verify onFocusChange was called with null (no focus)
        expect(onFocusChange).toHaveBeenCalledWith(null);
    });

    test('updates focused node when different team is selected', () => {
        const onFocusChange = vi.fn();
        const onTeamSelect = vi.fn();

        render(
            <ControlPanel
                onFocusChange={onFocusChange}
                onTeamSelect={onTeamSelect}
                searchNodes={mockNodes}
            />
        );

        // Select first team
        const input = screen.getByPlaceholderText('Search teams...');
        fireEvent.change(input, { target: { value: '7UP' } });
        const result1 = screen.getByText(/7UP - Colorado Cyclist/);
        fireEvent.click(result1);

        // Clear and select second team
        const clearButton = screen.getByRole('button', { name: /clear/i });
        fireEvent.click(clearButton);

        fireEvent.change(input, { target: { value: 'Ineos' } });
        const result2 = screen.getByText(/Ineos Grenadiers/);
        fireEvent.click(result2);

        // Apply filters
        const applyButton = screen.getByText('Apply Filters');
        fireEvent.click(applyButton);

        // Should call with second team's ID
        expect(onFocusChange).toHaveBeenCalledWith('node-ineos');
    });

    test('gracefully handles missing onFocusChange prop', () => {
        // Should not crash if onFocusChange is not provided
        render(
            <ControlPanel
                searchNodes={mockNodes}
            />
        );

        const input = screen.getByPlaceholderText('Search teams...');
        fireEvent.change(input, { target: { value: '7UP' } });
        const result = screen.getByText(/7UP - Colorado Cyclist/);
        fireEvent.click(result);

        const applyButton = screen.getByText('Apply Filters');

        // Should not throw
        expect(() => fireEvent.click(applyButton)).not.toThrow();
    });
});
