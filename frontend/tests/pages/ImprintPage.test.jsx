import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ImprintPage from '../../src/pages/ImprintPage';

describe('ImprintPage', () => {
    it('renders German content by default', () => {
        render(<ImprintPage />);

        // Check for German headers
        expect(screen.getByText('Impressum')).toBeInTheDocument();
        expect(screen.getByText('Datenschutzerklärung')).toBeInTheDocument();

        // Check for German specific text in Google OAuth section
        expect(screen.getByText(/Die Nutzung und Übertragung von Informationen/)).toBeInTheDocument();
    });

    it('switches to English content when language toggle is clicked', () => {
        render(<ImprintPage />);

        // Find the toggle button (we'll need to add an aria-label or testid to it)
        const toggleButton = screen.getByRole('button', { name: /switch to english/i });
        fireEvent.click(toggleButton);

        // Check for English headers
        expect(screen.getByText('Legal Notice')).toBeInTheDocument();
        expect(screen.getByText('Privacy Policy')).toBeInTheDocument();

        // Check for English specific text in Google OAuth section
        // "The use and transfer to any other app of information received from Google APIs will adhere to Google API Services User Data Policy, including the Limited Use requirements."
        expect(screen.getByText(/The use and transfer to any other app of information received from Google APIs/)).toBeInTheDocument();

        // Check for specific data collection disclosure in English
        expect(screen.getByText(/We only collect your full name, email address, and profile picture/)).toBeInTheDocument();
    });
});
