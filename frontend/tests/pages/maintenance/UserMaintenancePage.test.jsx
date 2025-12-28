import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import UserMaintenancePage from '../../../src/pages/maintenance/UserMaintenancePage';
import { MemoryRouter } from 'react-router-dom';
import * as usersApi from '../../../src/api/users';
import '@testing-library/jest-dom';

// Mock the API
vi.mock('../../../src/api/users', () => ({
    getUsers: vi.fn(),
    updateUser: vi.fn()
}));

// Mock Auth Context
vi.mock('../../../src/contexts/AuthContext', () => ({
    useAuth: () => ({
        user: { id: 'admin-id', role: 'ADMIN' },
        isAdmin: () => true,
        isEditor: () => true,
        loading: false
    }),
    AuthProvider: ({ children }) => <>{children}</>
}));

const renderPage = () => {
    return render(
        <MemoryRouter>
            <UserMaintenancePage />
        </MemoryRouter>
    );
};

describe('UserMaintenancePage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders loading state initially', () => {
        // Mock promise that doesn't resolve immediately
        usersApi.getUsers.mockReturnValue(new Promise(() => { }));
        renderPage();
        expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('renders user list after fetching', async () => {
        const mockUsers = {
            items: [
                { user_id: 'u1', display_name: 'User One', email: 'u1@test.com', role: 'EDITOR', is_banned: false },
                { user_id: 'u2', display_name: 'User Two', email: 'u2@test.com', role: 'ADMIN', is_banned: true }
            ],
            total: 2
        };
        usersApi.getUsers.mockResolvedValue(mockUsers);

        renderPage();

        await waitFor(() => {
            const loading = screen.queryByText(/loading/i);
            expect(loading).not.toBeInTheDocument();
        });

        expect(screen.getByText('User One')).toBeInTheDocument();
        expect(screen.getByText('u1@test.com')).toBeInTheDocument();
        expect(screen.getByText('EDITOR')).toBeInTheDocument();

        expect(screen.getByText('User Two')).toBeInTheDocument();
    });
});
