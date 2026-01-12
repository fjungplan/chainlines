import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import DrivetrainSpinner from '../../src/components/DrivetrainSpinner';

describe('DrivetrainSpinner', () => {
    it('renders the drivetrain svg container', () => {
        const { container } = render(<DrivetrainSpinner />);
        const svg = container.querySelector('svg.drivetrain-spinner');
        expect(svg).toBeTruthy();
    });

    it('contains the essential parts: chainring, cassette, chain, derailleur', () => {
        const { container } = render(<DrivetrainSpinner />);
        // Check for specific drivetrain parts
        expect(container.querySelector('.chainring')).toBeTruthy(); // Front gear group
        expect(container.querySelector('.cassette')).toBeTruthy();  // Rear gear group
        expect(container.querySelectorAll('.chain').length).toBeGreaterThan(0);     // Chain path(s)
        expect(container.querySelector('.derailleur')).toBeTruthy();// Rear mech group
    });
});
