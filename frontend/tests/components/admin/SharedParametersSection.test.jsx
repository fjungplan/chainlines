import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SharedParametersSection from '../../../src/components/SharedParametersSection';

describe('SharedParametersSection', () => {
    const mockConfig = {
        SEARCH_RADIUS: 50,
        TARGET_RADIUS: 10,
        WEIGHTS: {
            ATTRACTION: 1000.0,
            CUT_THROUGH: 10000.0,
            BLOCKER: 5000.0,
            Y_SHAPE: 500.0,
            LANE_SHARING: 1000.0,
            OVERLAP_BASE: 500000.0,
            OVERLAP_FACTOR: 10000.0
        }
    };

    it('renders all sliders with correct initial values', () => {
        render(
            <SharedParametersSection
                config={mockConfig}
                onChange={() => { }}
            />
        );

        // Check SEARCH_RADIUS slider
        const searchSlider = screen.getByLabelText(/Search Radius/i);
        expect(searchSlider).toHaveValue('50');

        // Check TARGET_RADIUS slider
        const targetSlider = screen.getByLabelText(/Target Radius/i);
        expect(targetSlider).toHaveValue('10');

        // Check weight sliders
        expect(screen.getByLabelText(/Attraction/i)).toHaveValue('1000');
        expect(screen.getByLabelText(/Cut Through/i)).toHaveValue('10000');
        expect(screen.getByLabelText(/Blocker/i)).toHaveValue('5000');
    });

    it('calls onChange with updated config when slider changes', () => {
        const handleChange = vi.fn();
        render(
            <SharedParametersSection
                config={mockConfig}
                onChange={handleChange}
            />
        );

        const searchSlider = screen.getByLabelText(/Search Radius/i);
        fireEvent.change(searchSlider, { target: { value: '75' } });

        expect(handleChange).toHaveBeenCalledWith({
            ...mockConfig,
            SEARCH_RADIUS: 75
        });
    });

    it('calls onChange with updated weight when weight slider changes', () => {
        const handleChange = vi.fn();
        render(
            <SharedParametersSection
                config={mockConfig}
                onChange={handleChange}
            />
        );

        const attractionSlider = screen.getByLabelText(/Attraction/i);
        fireEvent.change(attractionSlider, { target: { value: '2000' } });

        expect(handleChange).toHaveBeenCalledWith({
            ...mockConfig,
            WEIGHTS: {
                ...mockConfig.WEIGHTS,
                ATTRACTION: 2000
            }
        });
    });

    it('displays all weight labels', () => {
        render(
            <SharedParametersSection
                config={mockConfig}
                onChange={() => { }}
            />
        );

        expect(screen.getByText(/Attraction/i)).toBeInTheDocument();
        expect(screen.getByText(/Cut Through/i)).toBeInTheDocument();
        expect(screen.getByText(/Blocker/i)).toBeInTheDocument();
        expect(screen.getByText(/Y Shape/i)).toBeInTheDocument();
        expect(screen.getByText(/Lane Sharing/i)).toBeInTheDocument();
        expect(screen.getByText(/Overlap Base/i)).toBeInTheDocument();
        expect(screen.getByText(/Overlap Factor/i)).toBeInTheDocument();
    });
});
