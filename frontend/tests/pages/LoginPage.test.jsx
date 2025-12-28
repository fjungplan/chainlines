import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from '../../src/pages/auth/LoginPage';

// Mock mocks
vi.mock('@react-oauth/google', () => ({
    GoogleLogin: () => <button>Mock Google Login</button>,
}));

vi.mock('../../src/contexts/AuthContext', () => ({
    useAuth: () => ({
        handleGoogleSuccess: vi.fn(),
    }),
}));

describe('LoginPage', () => {
    it('renders correctly', () => {
        render(
            <MemoryRouter>
                <LoginPage />
            </MemoryRouter>
        );
        expect(screen.getByText(/Sign in to contribute/i)).toBeInTheDocument();
        expect(screen.getByText(/Mock Google Login/i)).toBeInTheDocument();
    });
});
