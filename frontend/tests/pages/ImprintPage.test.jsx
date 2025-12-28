import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import '@testing-library/jest-dom';
import ImprintPage from '../../src/pages/ImprintPage';

describe('ImprintPage', () => {
    it('renders correctly', () => {
        render(<ImprintPage />);
        // Use getByRole to find the page title Card (expected single match)
        expect(screen.getByRole('heading', { name: /Datenschutzerklärung/i })).toBeInTheDocument();
    });
});
