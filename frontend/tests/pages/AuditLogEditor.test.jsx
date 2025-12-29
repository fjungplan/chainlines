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
        reapply: vi.fn()
    }
}));

// Mock child components
vi.mock('../../src/components/audit-log/DiffTable', () => ({
    default: () => <div data-testid="diff-table">Detail Diff</div>
}));
vi.mock('../../src/components/ErrorDisplay', () => ({
    ErrorDisplay: ({ error }) => <div data-testid="error-display">{typeof error === 'string' ? error : error.message}</div>
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

    it('handles interaction - revert', async () => {
        renderPage();
        await waitFor(() => expect(screen.getByText('Revert Edit')).toBeInTheDocument());

        // Mock confirmed reload returning reverted state
        auditLogApi.getDetail
            .mockResolvedValueOnce({ data: { ...mockEdit } }) // First load
            .mockResolvedValueOnce({ data: { ...mockEdit, status: 'REVERTED', can_revert: false } }); // Reload

        // Confirm dialog
        vi.spyOn(window, 'confirm').mockReturnValue(true);

        fireEvent.click(screen.getByText('Revert Edit'));

        await waitFor(() => {
            expect(auditLogApi.revert).toHaveBeenCalledWith('edit-123', expect.objectContaining({ notes: expect.any(String) }));
        });

        // Should trigger reload
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
            expect(errorDisplay).toHaveTextContent(/Failed to load edit/i);
        });
    });
});
