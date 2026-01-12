import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TeamMaintenancePage from '../../../src/pages/maintenance/TeamMaintenancePage';
import { teamsApi } from '../../../src/api/teams';
import { AuthProvider } from '../../../src/contexts/AuthContext';
import { MemoryRouter } from 'react-router-dom';

// Mock the API
vi.mock('../../../src/api/teams', () => ({
    teamsApi: {
        getTeams: vi.fn(),
    }
}));

// Mock the AuthContext
vi.mock('../../../src/contexts/AuthContext', () => ({
    useAuth: () => ({
        user: { name: 'Admin' },
        isEditor: () => true,
        isAdmin: () => true,
    }),
    AuthProvider: ({ children }) => <div>{children}</div>
}));

describe('TeamMaintenancePage Search', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        teamsApi.getTeams.mockResolvedValue({
            items: [
                { node_id: '1', legal_name: 'Peugeot', founding_year: 1900, is_active: true },
                { node_id: '2', legal_name: 'Cervelo', founding_year: 2000, is_active: false }
            ],
            total: 2
        });
    });

    it('renders the search input', async () => {
        render(
            <MemoryRouter>
                <TeamMaintenancePage />
            </MemoryRouter>
        );

        const searchInput = screen.getByPlaceholderText(/Search teams.../i);
        expect(searchInput).toBeInTheDocument();
    });

    it('triggers a debounced search when typing', async () => {
        render(
            <MemoryRouter>
                <TeamMaintenancePage />
            </MemoryRouter>
        );

        const searchInput = screen.getByPlaceholderText(/Search teams.../i);

        // Wait for initial load
        await waitFor(() => expect(teamsApi.getTeams).toHaveBeenCalledWith({ limit: 100 }));

        // Type into search
        fireEvent.change(searchInput, { target: { value: 'Peugeot' } });

        // Should NOT be called immediately due to debouncing (assuming 500ms debounce)
        expect(teamsApi.getTeams).toHaveBeenCalledTimes(1);

        // Wait for debounce and check call
        await waitFor(() => {
            expect(teamsApi.getTeams).toHaveBeenCalledWith(expect.objectContaining({
                search: 'Peugeot'
            }));
        }, { timeout: 1500 });

        expect(teamsApi.getTeams).toHaveBeenCalledTimes(2);
    });
});
