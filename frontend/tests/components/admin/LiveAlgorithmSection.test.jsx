import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import LiveAlgorithmSection from '../../../src/components/admin/LiveAlgorithmSection';

describe('LiveAlgorithmSection', () => {
    const mockConfig = {
        GROUPWISE: {
            MIN_FAMILY_SIZE: 3,
            MIN_LINKS: 2,
            ENABLE_SCOREBOARD: true
        },
        PASS_SCHEDULE: [
            {
                strategies: ['PARENTS', 'CHILDREN'],
                iterations: 100,
                min_family_size: 3,
                min_links: 2
            }
        ]
    };

    it('renders Groupwise parameters', () => {
        render(
            <LiveAlgorithmSection
                config={mockConfig}
                onChange={() => { }}
            />
        );

        expect(screen.getByLabelText(/Min Family Size/i)).toHaveValue(3);
        expect(screen.getByLabelText(/Min Links/i)).toHaveValue(2);
    });

    it('renders scoreboard toggle', () => {
        render(
            <LiveAlgorithmSection
                config={mockConfig}
                onChange={() => { }}
            />
        );

        const toggle = screen.getByRole('checkbox', { name: /Enable Scoreboard/i });
        expect(toggle).toBeChecked();
    });

    it('renders PassScheduleGrid', () => {
        render(
            <LiveAlgorithmSection
                config={mockConfig}
                onChange={() => { }}
            />
        );

        // PassScheduleGrid should be present
        expect(screen.getByRole('button', { name: /add pass/i })).toBeInTheDocument();
    });

    it('calls onChange when Groupwise params change', () => {
        const handleChange = vi.fn();
        render(
            <LiveAlgorithmSection
                config={mockConfig}
                onChange={handleChange}
            />
        );

        const minFamilyInput = screen.getByLabelText(/Min Family Size/i);
        fireEvent.change(minFamilyInput, { target: { value: '5' } });

        expect(handleChange).toHaveBeenCalled();
        const updatedConfig = handleChange.mock.calls[0][0];
        expect(updatedConfig.GROUPWISE.MIN_FAMILY_SIZE).toBe(5);
    });

    it('calls onChange when scoreboard toggle changes', () => {
        const handleChange = vi.fn();
        render(
            <LiveAlgorithmSection
                config={mockConfig}
                onChange={handleChange}
            />
        );

        const toggle = screen.getByRole('checkbox', { name: /Enable Scoreboard/i });
        fireEvent.click(toggle);

        expect(handleChange).toHaveBeenCalled();
        const updatedConfig = handleChange.mock.calls[0][0];
        expect(updatedConfig.GROUPWISE.ENABLE_SCOREBOARD).toBe(false);
    });

    it('calls onChange when PassScheduleGrid changes', () => {
        const handleChange = vi.fn();
        render(
            <LiveAlgorithmSection
                config={mockConfig}
                onChange={handleChange}
            />
        );

        const addButton = screen.getByRole('button', { name: /add pass/i });
        fireEvent.click(addButton);

        expect(handleChange).toHaveBeenCalled();
        const updatedConfig = handleChange.mock.calls[0][0];
        expect(updatedConfig.PASS_SCHEDULE.length).toBe(2);
    });
});
