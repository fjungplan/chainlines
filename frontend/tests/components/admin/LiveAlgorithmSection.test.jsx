import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import LiveAlgorithmSection from '../../../src/components/admin/LiveAlgorithmSection';

describe('LiveAlgorithmSection', () => {
    const mockConfig = {
        GROUPWISE: {
            MAX_RIGID_DELTA: 20,
            SA_MAX_ITER: 50,
            SA_INITIAL_TEMP: 100,
            SEARCH_RADIUS: 10
        },
        SCOREBOARD: {
            ENABLED: true
        },
        PASS_SCHEDULE: [
            {
                strategies: ['PARENTS', 'CHILDREN'],
                iterations: 100,
                minFamilySize: 3,
                minLinks: 2
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

        expect(screen.getByLabelText(/Max Rigid Delta/i)).toHaveValue(20);
        expect(screen.getByLabelText(/SA Max Iterations/i)).toHaveValue(50);
        expect(screen.getByLabelText(/SA Initial Temp/i)).toHaveValue(100);
        expect(screen.getByLabelText(/Search Radius/i)).toHaveValue(10);
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

        const deltaInput = screen.getByLabelText(/Max Rigid Delta/i);
        fireEvent.change(deltaInput, { target: { value: '25' } });

        expect(handleChange).toHaveBeenCalled();
        const updatedConfig = handleChange.mock.calls[0][0];
        expect(updatedConfig.GROUPWISE.MAX_RIGID_DELTA).toBe(25);
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
