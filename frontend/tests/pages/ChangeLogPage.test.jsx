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

    it('displays all major deployment milestones', () => {
        render(<ChangeLogPage />);
        expect(screen.getByText(/v0.9.3 - 2026-02-06: Versioning & Transparency/i)).toBeInTheDocument();
        expect(screen.getByText(/v0.9.0 - 2026-02-05: Multi-Profile Optimization Engine/i)).toBeInTheDocument();
        expect(screen.getByText(/v0.8.6 - 2026-02-03: Layout & API Stabilization/i)).toBeInTheDocument();
        expect(screen.getByText(/v0.8.5 - 2026-01-16: Scraper & Admin Deployment/i)).toBeInTheDocument();
        expect(screen.getByText(/v0.6.2 - 2025-12-18: Production Environment Setup/i)).toBeInTheDocument();
        expect(screen.getByText(/v0.5.1 - 2025-12-08: Initial Production Push/i)).toBeInTheDocument();
    });
});
