import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AuditLogPage from '../../src/pages/AuditLogPage';
import { MemoryRouter } from 'react-router-dom';
import { auditLogApi } from '../../src/api/auditLog';
import '@testing-library/jest-dom';

// Mock API
vi.mock('../../src/api/auditLog', () => ({
    auditLogApi: {
        getList: vi.fn(),
        getPendingCount: vi.fn(),
        getDetail: vi.fn(),
    }
}));

// Mock Auth
vi.mock('../../src/contexts/AuthContext', () => ({
    useAuth: () => ({
        user: { id: 'admin-id', role: 'ADMIN' },
        isAdmin: () => true,
        isModerator: () => true,
        loading: false
    })
}));

const renderPage = () => {
    return render(
        <MemoryRouter>
            <AuditLogPage />
        </MemoryRouter>
    );
};

describe('AuditLogPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Default mocks
        auditLogApi.getList.mockResolvedValue({
            data: {
                items: [],
                total: 0
            }
        });
        auditLogApi.getPendingCount.mockResolvedValue({ data: { count: 5 } });
    });

    it('renders and fetches data', async () => {
        renderPage();

        expect(screen.getByRole('heading', { name: "Audit Log" })).toBeInTheDocument();
        // We expect "5 pending" badge
        await waitFor(() => {
            expect(screen.getByText(/5 pending/i)).toBeInTheDocument();
        });

        expect(auditLogApi.getList).toHaveBeenCalledWith(
            expect.objectContaining({ status: ['PENDING'] })
        );
    });

    it('filters by status', async () => {
        renderPage();
        await waitFor(() => expect(auditLogApi.getList).toHaveBeenCalled());

        // Click 'Approved' button
        const approvedBtn = screen.getByRole('button', { name: 'Approved' });
        fireEvent.click(approvedBtn);

        await waitFor(() => {
            // Should be called with status=['PENDING', 'APPROVED']
            expect(auditLogApi.getList).toHaveBeenCalledWith(
                expect.objectContaining({
                    status: expect.arrayContaining(['PENDING', 'APPROVED'])
                })
            );
        });
    });

    it('filters by entity type', async () => {
        renderPage();
        await waitFor(() => expect(auditLogApi.getList).toHaveBeenCalled());

        // Select 'Team' from dropdown (value: team_node)
        const selects = document.querySelectorAll('select');
        const entitySelect = selects[0]; // Assuming only one select for now

        fireEvent.change(entitySelect, { target: { value: 'team_node' } });

        await waitFor(() => {
            expect(auditLogApi.getList).toHaveBeenCalledWith(
                expect.objectContaining({
                    entity_type: 'team_node'
                })
            );
        });
    });

    it('filters by date range', async () => {
        renderPage();
        await waitFor(() => expect(auditLogApi.getList).toHaveBeenCalled());

        const dateInputs = document.querySelectorAll('input[type="date"]');
        const startDateInput = dateInputs[0];
        const endDateInput = dateInputs[1];

        // Set start date
        fireEvent.change(startDateInput, { target: { value: '2023-01-01' } });

        await waitFor(() => {
            expect(auditLogApi.getList).toHaveBeenCalledWith(
                expect.objectContaining({
                    start_date: expect.stringContaining('2023-01-01')
                })
            );
        });

        // Set end date
        fireEvent.change(endDateInput, { target: { value: '2023-01-31' } });

        await waitFor(() => {
            // End date logic adds time info, but stringContaining should catch the date part
            expect(auditLogApi.getList).toHaveBeenCalledWith(
                expect.objectContaining({
                    end_date: expect.stringContaining('2023-01-31')
                })
            );
        });
    });

    it('sorts by columns', async () => {
        renderPage();
        await waitFor(() => expect(auditLogApi.getList).toHaveBeenCalled());

        // Default sort is created_at desc.
        // Sort by Action
        // Use exact match to avoid matching "Actions" column
        const actionHeader = screen.getByText('Action');
        fireEvent.click(actionHeader);

        await waitFor(() => {
            expect(auditLogApi.getList).toHaveBeenCalledWith(
                expect.objectContaining({
                    sort_by: 'action',
                    sort_order: 'desc'
                })
            );
        });

        // Click again -> asc. Text should now include down arrow "Action ↓"
        const actionHeaderDesc = screen.getByText('Action ↓');
        fireEvent.click(actionHeaderDesc);

        await waitFor(() => {
            expect(auditLogApi.getList).toHaveBeenCalledWith(
                expect.objectContaining({
                    sort_by: 'action',
                    sort_order: 'asc'
                })
            );
        });
    });

    it('handles pagination', async () => {
        // Mock with total items > pageSize (50)
        auditLogApi.getList.mockResolvedValue({
            data: {
                items: [],
                total: 100
            }
        });

        renderPage();
        await waitFor(() => expect(auditLogApi.getList).toHaveBeenCalled());

        const nextBtn = screen.getByRole('button', { name: 'Next' });
        expect(nextBtn).not.toBeDisabled();

        fireEvent.click(nextBtn);

        await waitFor(() => {
            // Page 2: skip=50
            expect(auditLogApi.getList).toHaveBeenCalledWith(
                expect.objectContaining({
                    skip: 50,
                    limit: 50
                })
            );
        });

        // Change page size to 25
        const sizeSelect = screen.getByRole('combobox', { name: 'Items per page' });
        fireEvent.change(sizeSelect, { target: { value: '25' } });

        await waitFor(() => {
            // Reset to page 1, with limit 25
            expect(auditLogApi.getList).toHaveBeenCalledWith(
                expect.objectContaining({
                    skip: 0,
                    limit: 25
                })
            );
        });
    });
});
