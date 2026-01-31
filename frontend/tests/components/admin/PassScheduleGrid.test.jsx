import { render, screen, fireEvent, within } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import PassScheduleGrid from '../../../src/components/admin/PassScheduleGrid';

describe('PassScheduleGrid', () => {
    const mockSchedule = [
        {
            strategies: ['PARENTS', 'CHILDREN'],
            iterations: 100,
            minFamilySize: 3,
            minLinks: 2
        },
        {
            strategies: ['HYBRID'],
            iterations: 50,
            minFamilySize: 5,
            minLinks: 3
        }
    ];

    it('renders all rows with correct values', () => {
        render(
            <PassScheduleGrid
                schedule={mockSchedule}
                onChange={() => { }}
            />
        );

        // Check that all expected values are present
        expect(screen.getByDisplayValue('100')).toBeInTheDocument();
        expect(screen.getAllByDisplayValue('3').length).toBeGreaterThan(0);
        expect(screen.getByDisplayValue('50')).toBeInTheDocument();
        expect(screen.getByDisplayValue('5')).toBeInTheDocument();
    });

    it('displays selected strategies for each row', () => {
        render(
            <PassScheduleGrid
                schedule={mockSchedule}
                onChange={() => { }}
            />
        );

        // Check that strategy labels are present (multiple instances expected)
        expect(screen.getAllByText(/PARENTS/).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/CHILDREN/).length).toBeGreaterThan(0);
        expect(screen.getAllByText(/HYBRID/).length).toBeGreaterThan(0);
    });

    it('adds a new row when Add Pass button is clicked', () => {
        const handleChange = vi.fn();
        render(
            <PassScheduleGrid
                schedule={mockSchedule}
                onChange={handleChange}
            />
        );

        const addButton = screen.getByRole('button', { name: /add pass/i });
        fireEvent.click(addButton);

        expect(handleChange).toHaveBeenCalledWith([
            ...mockSchedule,
            {
                strategies: [],
                iterations: 100,
                minFamilySize: 3,
                minLinks: 2
            }
        ]);
    });

    it('removes a row when Remove button is clicked', () => {
        const handleChange = vi.fn();
        render(
            <PassScheduleGrid
                schedule={mockSchedule}
                onChange={handleChange}
            />
        );

        const removeButtons = screen.getAllByRole('button', { name: /remove/i });
        fireEvent.click(removeButtons[0]);

        expect(handleChange).toHaveBeenCalledWith([mockSchedule[1]]);
    });

    it('disables other strategies when HYBRID is selected', () => {
        const singleRowSchedule = [{
            strategies: [],
            iterations: 100,
            minFamilySize: 3,
            minLinks: 2
        }];

        const handleChange = vi.fn();
        const { rerender } = render(
            <PassScheduleGrid
                schedule={singleRowSchedule}
                onChange={handleChange}
            />
        );

        // Find and click the HYBRID checkbox
        const hybridCheckbox = screen.getByRole('checkbox', { name: /HYBRID/i });
        fireEvent.click(hybridCheckbox);

        // Verify HYBRID was added
        expect(handleChange).toHaveBeenCalled();
        const updatedSchedule = handleChange.mock.calls[0][0];
        expect(updatedSchedule[0].strategies).toEqual(['HYBRID']);

        // Re-render with HYBRID selected
        rerender(
            <PassScheduleGrid
                schedule={updatedSchedule}
                onChange={handleChange}
            />
        );

        // Other checkboxes should be disabled
        const parentsCheckbox = screen.getByRole('checkbox', { name: /PARENTS/i });
        expect(parentsCheckbox).toBeDisabled();
    });

    it('disables HYBRID when other strategies are selected', () => {
        const singleRowSchedule = [{
            strategies: [],
            iterations: 100,
            minFamilySize: 3,
            minLinks: 2
        }];

        const handleChange = vi.fn();
        const { rerender } = render(
            <PassScheduleGrid
                schedule={singleRowSchedule}
                onChange={handleChange}
            />
        );

        // Click PARENTS checkbox
        const parentsCheckbox = screen.getByRole('checkbox', { name: /PARENTS/i });
        fireEvent.click(parentsCheckbox);

        // Verify PARENTS was added
        expect(handleChange).toHaveBeenCalled();
        const updatedSchedule = handleChange.mock.calls[0][0];
        expect(updatedSchedule[0].strategies).toContain('PARENTS');

        // Re-render with PARENTS selected
        rerender(
            <PassScheduleGrid
                schedule={updatedSchedule}
                onChange={handleChange}
            />
        );

        // HYBRID should be disabled
        const hybridCheckbox = screen.getByRole('checkbox', { name: /HYBRID/i });
        expect(hybridCheckbox).toBeDisabled();
    });

    it('updates iterations when input changes', () => {
        const handleChange = vi.fn();
        render(
            <PassScheduleGrid
                schedule={mockSchedule}
                onChange={handleChange}
            />
        );

        const iterationsInput = screen.getByDisplayValue('100');
        fireEvent.change(iterationsInput, { target: { value: '200' } });

        expect(handleChange).toHaveBeenCalled();
        const updatedSchedule = handleChange.mock.calls[0][0];
        expect(updatedSchedule[0].iterations).toBe(200);
    });
});
