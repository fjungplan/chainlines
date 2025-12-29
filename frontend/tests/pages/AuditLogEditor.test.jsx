import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import AuditLogEditor from '../../src/pages/AuditLogEditor';
import { auditLogApi } from '../../src/api/auditLog';
import { useAuth } from '../../src/contexts/AuthContext';

vi.mock('../../src/components/common/Button', () => ({ default: (props) => <button {...props} /> }));
vi.mock('../../src/contexts/AuthContext');

// Manual mock for API
vi.mock('../../src/api/auditLog', () => ({
    auditLogApi: {
        getDetail: vi.fn(),
        revert: vi.fn(),
        reapply: vi.fn(),
        review: vi.fn()
    }
}));

// Mock child components
vi.mock('../../src/components/audit-log/DiffTable', () => ({
    default: () => <div data-testid="diff-table">Detail Diff</div>
}));
vi.mock('../../src/components/ErrorDisplay', () => ({
    ErrorDisplay: ({ error }) => <div data-testid="error-display">{typeof error === 'string' ? error : error.message}</div>
}));
vi.mock('../../src/components/moderation/ReviewModal', () => ({
    default: ({ onConfirm }) => (
        <div data-testid="review-modal">
            <button onClick={() => onConfirm('LGTM')}>Confirm Review</button>
        </div>
    )
}));

describe('AuditLogEditor', () => {
    const mockEdit = {
        edit_id: 'edit-123',
        entity_type: 'team_node',
        entity_name: 'Test Team',
        action: 'UPDATE',
        status: 'APPROVED',
        submitted_by: { display_name: 'User 1', email: 'u1@example.com' },
        submitted_at: '2023-01-01T00:00:00Z',
        reviewed_by: { display_name: 'Admin 1' },
        reviewed_at: '2023-01-02T00:00:00Z',
        snapshot_before: { name: 'Old' },
        snapshot_after: { name: 'New' },
        can_revert: true,
        summary: 'Updated name'
    };

    beforeEach(() => {
        vi.clearAllMocks();
        // Setup Auth (not used directly in component but good practice for context)
        useAuth.mockReturnValue({ isAdmin: () => true, isModerator: () => true });
        // Setup API
        auditLogApi.getDetail.mockResolvedValue({ data: { ...mockEdit } });
        auditLogApi.revert.mockResolvedValue({ data: { status: 'REVERTED' } });
        auditLogApi.reapply.mockResolvedValue({ data: { status: 'PENDING' } });
        auditLogApi.review.mockResolvedValue({});
    });

    const renderPage = (editId = 'edit-123') => {
        render(
            <MemoryRouter initialEntries={[`/audit-log/${editId}`]}>
                <Routes>
                    <Route path="/audit-log/:editId" element={<AuditLogEditor />} />
                </Routes>
            </MemoryRouter>
        );
    };

    it('fetches and renders edit details', async () => {
        renderPage();

        // Initial loading state might be fast, wait for content
        await waitFor(() => {
            expect(auditLogApi.getDetail).toHaveBeenCalledWith('edit-123');
        });

        expect(screen.getByText('Test Team')).toBeInTheDocument();
        expect(screen.getByText('APPROVED')).toBeInTheDocument();
        expect(screen.getByText('User 1')).toBeInTheDocument();
        expect(screen.getByTestId('diff-table')).toBeInTheDocument();

        // Revert button should be present
        expect(screen.getByText('Revert Edit')).toBeInTheDocument();
    });

    it('handles interaction - approve', async () => {
        // Mock pending state
        auditLogApi.getDetail.mockResolvedValue({
            data: {
                ...mockEdit,
                status: 'PENDING',
                can_approve: true,
                can_reject: true,
                can_revert: false
            }
        });

        renderPage('edit-pending');

        await waitFor(() => expect(screen.getByText('Approve')).toBeInTheDocument());

        fireEvent.click(screen.getByText('Approve'));

        // Should open confirm modal
        await waitFor(() => expect(screen.getByTestId('review-modal')).toBeInTheDocument());

        // Simulate confirm in modal (ReviewModal mock calls onReview with notes)
        fireEvent.click(screen.getByText('Confirm Review'));

        await waitFor(() => {
            // Approve sends approved: true
            expect(auditLogApi.review).toHaveBeenCalledWith('edit-pending', expect.objectContaining({ approved: true }));
        });

        // Should reload
        await waitFor(() => {
            expect(auditLogApi.getDetail).toHaveBeenCalledTimes(2);
        });
    });

    it('handles interaction - reject', async () => {
        // Mock pending state
        auditLogApi.getDetail.mockResolvedValue({
            data: {
                ...mockEdit,
                status: 'PENDING',
                can_approve: true,
                can_reject: true,
                can_revert: false
            }
        });

        renderPage('edit-pending');

        await waitFor(() => expect(screen.getByText('Reject')).toBeInTheDocument());

        fireEvent.click(screen.getByText('Reject'));

        await waitFor(() => expect(screen.getByTestId('review-modal')).toBeInTheDocument());

        fireEvent.click(screen.getByText('Confirm Review'));

        await waitFor(() => {
            // Reject sends approved: false
            expect(auditLogApi.review).toHaveBeenCalledWith('edit-pending', expect.objectContaining({ approved: false }));
        });
    });

    it('handles interaction - revert', async () => {
        renderPage();
        await waitFor(() => expect(screen.getByText('Revert Edit')).toBeInTheDocument());

        // Mock confirmed reload returning reverted state
        auditLogApi.getDetail
            .mockResolvedValueOnce({ data: { ...mockEdit } }) // First load
            .mockResolvedValueOnce({ data: { ...mockEdit, status: 'REVERTED', can_revert: false } }); // Reload

        fireEvent.click(screen.getByText('Revert Edit'));

        // Modal should appear
        await waitFor(() => expect(screen.getByTestId('review-modal')).toBeInTheDocument());

        // Confirm
        fireEvent.click(screen.getByText('Confirm Review'));

        await waitFor(() => {
            expect(auditLogApi.revert).toHaveBeenCalledWith('edit-123', expect.objectContaining({ notes: expect.any(String) }));
        });

        // Should reload
        await waitFor(() => {
            expect(auditLogApi.getDetail).toHaveBeenCalledTimes(2);
        });
    });

    it('handles interaction - reapply', async () => {
        // Mock rejected state for reapply
        auditLogApi.getDetail
            .mockResolvedValueOnce({
                data: {
                    ...mockEdit,
                    status: 'REJECTED',
                    can_approve: false,
                    can_revert: false,
                    // Typically reapply is available for rejected/reverted
                }
            })
            .mockResolvedValueOnce({ data: { ...mockEdit, status: 'APPROVED' } }); // Reload

        renderPage('edit-rejected');

        await waitFor(() => expect(screen.getByText('Re-apply Edit')).toBeInTheDocument());

        fireEvent.click(screen.getByText('Re-apply Edit'));

        // Modal should appear
        await waitFor(() => expect(screen.getByTestId('review-modal')).toBeInTheDocument());

        // Confirm
        fireEvent.click(screen.getByText('Confirm Review'));

        await waitFor(() => {
            expect(auditLogApi.reapply).toHaveBeenCalledWith('edit-rejected', expect.objectContaining({ notes: expect.any(String) }));
        });

        // Should reload
        await waitFor(() => {
            expect(auditLogApi.getDetail).toHaveBeenCalledTimes(2);
        });
    });

    it('displays error state', async () => {
        auditLogApi.getDetail.mockReset();
        auditLogApi.getDetail.mockRejectedValue(new Error('Not found'));
        const { container } = render(
            <MemoryRouter initialEntries={['/audit-log/edit-123']}>
                <Routes>
                    <Route path="/audit-log/:editId" element={<AuditLogEditor />} />
                </Routes>
            </MemoryRouter>
        );

        await waitFor(() => {
            const errorDisplay = screen.getByTestId('error-display');
            expect(errorDisplay).toBeInTheDocument();
            // Expect the actual error message
            expect(errorDisplay).toHaveTextContent(/Not found/i);
        });
    });
});
