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

    it('fetches users after debounce delay on mount', async () => {
        // Mock isAdmin only (authLoading not needed anymore as per recent refactor)
        const isAdminResolved = vi.fn().mockReturnValue(true);
        authContext.useAuth.mockReturnValue({
            user: { name: 'Admin' },
            loading: false,
            isAdmin: isAdminResolved,
        });

        usersApi.getUsers.mockResolvedValue({
            items: [{ user_id: '123', display_name: 'Test User', email: 'test@example.com', role: 'EDITOR', is_banned: false }],
            total: 1
        });

        render(
            <MemoryRouter>
                <UserMaintenancePage />
            </MemoryRouter>
        );

        // Should call getUsers after delay
        await waitFor(() => {
            expect(usersApi.getUsers).toHaveBeenCalledWith({ search: '', limit: 100 });
        }, { timeout: 2000 });

        expect(screen.getByText('Test User')).toBeInTheDocument();
    });
});
