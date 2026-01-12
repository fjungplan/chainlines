import React from 'react';
import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import TeamDetailPage from '../../src/pages/TeamDetailPage';
import { AuthProvider } from '../../src/contexts/AuthContext';

// Mock hooks
vi.mock('../../src/hooks/useTeamData', () => ({
    useTeamHistory: vi.fn()
}));

vi.mock('../../src/contexts/AuthContext', async (importOriginal) => {
    const actual = await importOriginal();
    return {
        ...actual,
        useAuth: vi.fn(),
        AuthProvider: ({ children }) => <div>{children}</div>
    };
});

import { useTeamHistory } from '../../src/hooks/useTeamData';
import { useAuth } from '../../src/contexts/AuthContext';

describe('TeamDetailPage', () => {
    const mockData = {
        node_id: 'node-123',
        legal_name: 'Test Team',
        timeline: [
            {
                year: 2024,
                name: 'Test Team 2024',
                era_id: 'era-123',
                sponsors: [
                    {
                        brand_name: 'Sponsor A',
                        master_id: 'master-123',
                        color: '#ff0000'
                    }
                ]
            }
        ]
    };

    it('should render edit links for logged-in users', () => {
        useAuth.mockReturnValue({
            user: { email: 'admin@example.com' },
            isEditor: () => true,
            isAdmin: () => true
        });

        useTeamHistory.mockReturnValue({
            data: mockData,
            isLoading: false,
            error: null
        });

        render(
            <MemoryRouter initialEntries={['/team/node-123']}>
                <Routes>
                    <Route path="/team/:nodeId" element={<TeamDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        // Check for Era Edit Link
        const eraLink = screen.getByRole('link', { name: /Test Team 2024/i });
        expect(eraLink).toBeInTheDocument();
        expect(eraLink).toHaveAttribute('href', '/maintenance/teams?nodeId=node-123&eraId=era-123');

        // Check for Sponsor Edit Link
        const sponsorLink = screen.getByRole('link', { name: /Sponsor A/i });
        expect(sponsorLink).toBeInTheDocument();
        expect(sponsorLink).toHaveAttribute('href', '/maintenance/sponsors?edit=master-123');
    });

    it('should NOT render edit links for guests', () => {
        useAuth.mockReturnValue({
            user: null,
            isEditor: () => false,
            isAdmin: () => false
        });

        useTeamHistory.mockReturnValue({
            data: mockData,
            isLoading: false,
            error: null
        });

        render(
            <MemoryRouter initialEntries={['/team/node-123']}>
                <Routes>
                    <Route path="/team/:nodeId" element={<TeamDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        // Era name should just be text
        expect(screen.getByText('Test Team 2024')).toBeInTheDocument();
        // Should NOT have the edit link, so queryByRole should be null
        expect(screen.queryByRole('link', { name: /Test Team 2024/i })).not.toBeInTheDocument();
    });
});
