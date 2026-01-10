import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import UserMaintenancePage from '../../../src/pages/maintenance/UserMaintenancePage';
import * as usersApi from '../../../src/api/users';
import * as authContext from '../../../src/contexts/AuthContext';
import { MemoryRouter } from 'react-router-dom';

// Mock the API
vi.mock('../../../src/api/users', () => ({
    getUsers: vi.fn(),
}));

// Mock the AuthContext
vi.mock('../../../src/contexts/AuthContext', () => ({
    useAuth: vi.fn(),
}));

describe('UserMaintenancePage Initial Load', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('waits for auth loading to finish before fetching users', async () => {
        // Mock isAdmin false and loading true initially
        const isAdminMock = vi.fn().mockReturnValue(false);
        authContext.useAuth.mockReturnValue({
            user: null,
            loading: true,
            isAdmin: isAdminMock,
        });

        usersApi.getUsers.mockResolvedValue({
            items: [{ user_id: '123', display_name: 'Test User', email: 'test@example.com', role: 'EDITOR', is_banned: false }],
            total: 1
        });

        const { rerender } = render(
            <MemoryRouter>
                <UserMaintenancePage />
            </MemoryRouter>
        );

        // Should not show Access Denied yet (it might show loading spinner if we implemented it, or nothing)
        // But most importantly, it should NOT call getUsers
        expect(usersApi.getUsers).not.toHaveBeenCalled();

        // Simulate Auth resolution (Loading finished, is Admin)
        const isAdminResolved = vi.fn().mockReturnValue(true);
        authContext.useAuth.mockReturnValue({
            user: { name: 'Admin' },
            loading: false,
            isAdmin: isAdminResolved,
        });

        rerender(
            <MemoryRouter>
                <UserMaintenancePage />
            </MemoryRouter>
        );

        // Now it should trigger the fetch
        await waitFor(() => {
            expect(usersApi.getUsers).toHaveBeenCalled();
        }, { timeout: 2000 });

        expect(screen.getByText('Test User')).toBeInTheDocument();
    });
});
