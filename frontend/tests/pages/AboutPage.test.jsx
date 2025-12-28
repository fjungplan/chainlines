import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import '@testing-library/jest-dom';
import AboutPage from '../../src/pages/AboutPage';

describe('AboutPage', () => {
    it('renders correctly', () => {
        render(<AboutPage />);
        expect(screen.getByText(/About ChainLines/i)).toBeInTheDocument();
    });
});
