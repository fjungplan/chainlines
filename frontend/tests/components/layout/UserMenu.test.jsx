import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import UserMenu from '../../../src/components/layout/UserMenu';
import * as AuthContext from '../../../src/contexts/AuthContext';
import * as AuditLogContext from '../../../src/contexts/AuditLogContext';

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
    useNavigate: () => mockNavigate,
}));

// Mock contexts
vi.mock('../../../src/contexts/AuthContext', () => ({
    useAuth: vi.fn(),
}));

vi.mock('../../../src/contexts/AuditLogContext', () => ({
    useAuditLog: vi.fn(),
}));

// Mock DeleteAccountModal
vi.mock('../../../src/components/DeleteAccountModal', () => ({
    default: ({ isOpen, onClose }) => (
        isOpen ? <div data-testid="delete-account-modal"><button onClick={onClose}>Close</button></div> : null
    ),
}));

describe('UserMenu', () => {
    const mockUser = {
        email: 'test@example.com',
        display_name: 'Test User',
        avatar_url: 'http://example.com/avatar.jpg',
        approved_edits_count: 0
    };

    const mockLogout = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();

        AuthContext.useAuth.mockReturnValue({
            user: mockUser,
            logout: mockLogout,
            isAdmin: () => false,
            isModerator: () => false,
            canEdit: () => true,
            needsModeration: () => false
        });

        AuditLogContext.useAuditLog.mockReturnValue({
            pendingCount: 0
        });
    });

    it('renders delete account button in menu', () => {
        render(<UserMenu />);

        // Open menu
        fireEvent.click(screen.getByRole('button', { name: /test user/i }));

        // Check for delete button
        expect(screen.getByText('Delete Account')).toBeInTheDocument();
    });

    it('opens delete modal when clicked', () => {
        render(<UserMenu />);

        // Open menu
        fireEvent.click(screen.getByRole('button', { name: /test user/i }));

        // Click delete
        fireEvent.click(screen.getByText('Delete Account'));

        // Check modal
        expect(screen.getByTestId('delete-account-modal')).toBeInTheDocument();

        // Close modal
        fireEvent.click(screen.getByText('Close'));
        expect(screen.queryByTestId('delete-account-modal')).not.toBeInTheDocument();
    });
});
