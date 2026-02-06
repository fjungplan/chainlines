import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import '@testing-library/jest-dom';
import ChangeLogPage from '../../src/pages/ChangeLogPage';

describe('ChangeLogPage', () => {
    it('renders the Change Log title', () => {
        render(<ChangeLogPage />);
        expect(screen.getByRole('heading', { name: /Project Change Log/i })).toBeInTheDocument();
    });

    it('displays version 0.9.3 section', () => {
        render(<ChangeLogPage />);
        expect(screen.getByText(/v0.9.3/i)).toBeInTheDocument();
    });
});
