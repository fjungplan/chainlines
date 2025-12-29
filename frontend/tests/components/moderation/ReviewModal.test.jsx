import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom';
import ReviewModal from '../../../src/components/moderation/ReviewModal';

// Mock dependencies
vi.mock('../../../src/components/common/Button', () => ({
    default: ({ children, ...props }) => <button {...props}>{children}</button>
}));

vi.mock('../../../src/utils/dateUtils', () => ({
    formatDateTime: (dateStr) => dateStr ? new Date(dateStr).toLocaleString() : '-'
}));

describe('ReviewModal', () => {
    const mockEdit = {
        edit_id: 'edit-123',
        entity_type: 'team_node',
        submitted_by: {
            display_name: 'Test User',
            email: 'test@example.com'
        },
        submitted_at: '2023-01-01T00:00:00Z',
        snapshot_after: {
            name: 'Updated Name',
            tier: 'WT'
        }
    };

    const mockOnClose = vi.fn();
    const mockOnReview = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    const renderModal = (editOverrides = {}) => {
        const edit = { ...mockEdit, ...editOverrides };
        return render(
            <ReviewModal
                edit={edit}
                onClose={mockOnClose}
                onReview={mockOnReview}
            />
        );
    };

    describe('Rendering', () => {
        it('renders edit information correctly', () => {
            renderModal();

            expect(screen.getByText('Review Edit')).toBeInTheDocument();
            expect(screen.getByText('team_node')).toBeInTheDocument();
            expect(screen.getByText('Test User')).toBeInTheDocument();
            expect(screen.getByText(/2023/)).toBeInTheDocument();
        });

        it('renders snapshot_after as JSON', () => {
            renderModal();

            expect(screen.getByText(/"name": "Updated Name"/)).toBeInTheDocument();
        });
    });

    describe('User Interactions', () => {
        it('updates notes textarea', () => {
            renderModal();

            const textarea = screen.getByLabelText('Review notes');
            fireEvent.change(textarea, { target: { value: 'Test notes' } });

            expect(textarea.value).toBe('Test notes');
        });

        it('enables approve button without notes', () => {
            renderModal();

            const approveButton = screen.getByText('Approve & Apply');
            expect(approveButton).not.toBeDisabled();
        });

        it('disables reject button without notes', () => {
            renderModal();

            const rejectButton = screen.getByText('Reject');
            expect(rejectButton).toBeDisabled();
        });

        it('enables reject button with notes', () => {
            renderModal();

            const textarea = screen.getByLabelText('Review notes');
            fireEvent.change(textarea, { target: { value: 'Rejection reason' } });

            const rejectButton = screen.getByText('Reject');
            expect(rejectButton).not.toBeDisabled();
        });
    });

    describe('Approval Flow', () => {
        it('calls onReview with correct params when approved', async () => {
            mockOnReview.mockResolvedValue();
            renderModal();

            const textarea = screen.getByLabelText('Review notes');
            fireEvent.change(textarea, { target: { value: 'Looks good' } });

            const approveButton = screen.getByText('Approve & Apply');
            fireEvent.click(approveButton);

            await waitFor(() => {
                expect(mockOnReview).toHaveBeenCalledWith('edit-123', true, 'Looks good');
            });
        });

        it('calls onReview without notes when approved', async () => {
            mockOnReview.mockResolvedValue();
            renderModal();

            const approveButton = screen.getByText('Approve & Apply');
            fireEvent.click(approveButton);

            await waitFor(() => {
                expect(mockOnReview).toHaveBeenCalledWith('edit-123', true, '');
            });
        });

        it('disables buttons during approval', async () => {
            let resolveReview;
            mockOnReview.mockReturnValue(new Promise(resolve => { resolveReview = resolve; }));

            renderModal();

            const approveButton = screen.getByText('Approve & Apply');
            fireEvent.click(approveButton);

            await waitFor(() => {
                expect(approveButton).toBeDisabled();
            });

            resolveReview();
        });
    });

    describe('Rejection Flow', () => {
        it('shows validation error when rejecting without notes', async () => {
            renderModal();

            const rejectButton = screen.getByText('Reject');

            // Button should be disabled initially
            expect(rejectButton).toBeDisabled();

            // Try to enable it with whitespace only
            const textarea = screen.getByLabelText('Review notes');
            fireEvent.change(textarea, { target: { value: '   ' } });

            // Button is now enabled but clicking should show error
            fireEvent.click(rejectButton);

            await waitFor(() => {
                expect(screen.getByText('Rejection notes are required to explain your decision')).toBeInTheDocument();
            });

            expect(mockOnReview).not.toHaveBeenCalled();
        });

        it('calls onReview with correct params when rejected with notes', async () => {
            mockOnReview.mockResolvedValue();
            renderModal();

            const textarea = screen.getByLabelText('Review notes');
            fireEvent.change(textarea, { target: { value: 'Needs more info' } });

            const rejectButton = screen.getByText('Reject');
            fireEvent.click(rejectButton);

            await waitFor(() => {
                expect(mockOnReview).toHaveBeenCalledWith('edit-123', false, 'Needs more info');
            });
        });

        it('clears validation error when user starts typing', async () => {
            renderModal();

            const textarea = screen.getByLabelText('Review notes');

            // Trigger validation error
            fireEvent.change(textarea, { target: { value: '   ' } });
            const rejectButton = screen.getByText('Reject');
            fireEvent.click(rejectButton);

            await waitFor(() => {
                expect(screen.getByText('Rejection notes are required to explain your decision')).toBeInTheDocument();
            });

            // Start typing
            fireEvent.change(textarea, { target: { value: 'Actually...' } });

            // Error should be cleared
            expect(screen.queryByText('Rejection notes are required to explain your decision')).not.toBeInTheDocument();
        });

        it('adds validation-error class to textarea', async () => {
            renderModal();

            const textarea = screen.getByLabelText('Review notes');
            fireEvent.change(textarea, { target: { value: '   ' } });

            const rejectButton = screen.getByText('Reject');
            fireEvent.click(rejectButton);

            await waitFor(() => {
                expect(textarea).toHaveClass('validation-error');
            });
        });
    });

    describe('Modal Controls', () => {
        it('closes on Escape key', () => {
            renderModal();

            const modal = screen.getByRole('dialog');
            fireEvent.keyDown(modal, { key: 'Escape' });

            expect(mockOnClose).toHaveBeenCalled();
        });

        it('closes on overlay click', () => {
            const { container } = renderModal();

            const overlay = container.querySelector('.modal-overlay');
            fireEvent.click(overlay);

            expect(mockOnClose).toHaveBeenCalled();
        });

        it('does not close on modal content click', () => {
            const { container } = renderModal();

            const modalContent = container.querySelector('.modal-content');
            fireEvent.click(modalContent);

            expect(mockOnClose).not.toHaveBeenCalled();
        });

        it('calls onClose when close button clicked', () => {
            renderModal();

            const closeButton = screen.getByLabelText('Close');
            fireEvent.click(closeButton);

            expect(mockOnClose).toHaveBeenCalled();
        });

        it('focuses modal on mount', () => {
            const { container } = renderModal();

            const modal = container.querySelector('.modal-content');
            expect(document.activeElement).toBe(modal);
        });
    });
});
