import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DeleteAccountModal from '../../src/components/DeleteAccountModal';
import * as usersApi from '../../src/api/users';

vi.mock('../../src/api/users');

describe('DeleteAccountModal', () => {
    const mockOnClose = vi.fn();
    const mockOnDeleteSuccess = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders nothing when not open', () => {
        render(<DeleteAccountModal isOpen={false} onClose={mockOnClose} />);
        expect(screen.queryByText('Delete Account')).toBeNull();
    });

    it('renders confirmation text when open', () => {
        render(<DeleteAccountModal isOpen={true} onClose={mockOnClose} />);
        expect(screen.getByText('Delete Account')).toBeInTheDocument();
        expect(screen.getByText(/Are you sure you want to delete your account/)).toBeInTheDocument();
    });

    it('calls deleteAccount on confirmation', async () => {
        usersApi.deleteAccount.mockResolvedValue({});

        render(<DeleteAccountModal isOpen={true} onClose={mockOnClose} onDeleteSuccess={mockOnDeleteSuccess} />);

        // Click confirm
        fireEvent.click(screen.getByText('Delete Permanently'));

        // Should show loading state or similar, but eventually call api
        await waitFor(() => {
            expect(usersApi.deleteAccount).toHaveBeenCalled();
        });

        await waitFor(() => {
            expect(mockOnDeleteSuccess).toHaveBeenCalled();
        });
    });

    it('displays error message on failure', async () => {
        const errorMsg = 'Failed to delete';
        usersApi.deleteAccount.mockRejectedValue({ response: { data: { detail: errorMsg } } });

        render(<DeleteAccountModal isOpen={true} onClose={mockOnClose} />);

        fireEvent.click(screen.getByText('Delete Permanently'));

        await waitFor(() => {
            expect(screen.getByText(errorMsg)).toBeInTheDocument();
        });
    });
});
