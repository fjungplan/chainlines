import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import AdminOptimizer from '../../src/pages/AdminOptimizer';
import { optimizerApi } from '../../src/api/optimizer';
import '@testing-library/jest-dom';

// Mock API
vi.mock('../../src/api/optimizer', () => ({
    optimizerApi: {
        getFamilies: vi.fn(),
        triggerOptimization: vi.fn(),
        getStatus: vi.fn(),
    }
}));

const mockAuth = {
    isAdmin: () => true,
};

// Mock Auth
vi.mock('../../src/contexts/AuthContext', () => ({
    useAuth: () => mockAuth
}));

const renderPage = async () => {
    let result;
    await act(async () => {
        result = render(
            <MemoryRouter>
                <AdminOptimizer />
            </MemoryRouter>
        );
    });
    return result;
};

describe('AdminOptimizer Page', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.useRealTimers();

        // Default mocks
        optimizerApi.getFamilies.mockResolvedValue([
            {
                family_hash: 'hash1',
                node_count: 10,
                link_count: 5,
                score: 123.45,
                optimized_at: '2023-01-01T00:00:00Z',
                status: 'cached'
            }
        ]);
        optimizerApi.getStatus.mockResolvedValue({
            active_tasks: 0,
            last_run: '2023-01-01T00:00:00Z',
            last_error: null
        });
    });

    it('should display the page title', async () => {
        await renderPage();
        expect(screen.getByText(/Layout Optimizer/i)).toBeInTheDocument();
    });

    it('should allow checkbox selection', async () => {
        await renderPage();

        await waitFor(() => {
            expect(screen.getByText(/hash1/i)).toBeInTheDocument();
        });

        const checkboxes = screen.getAllByRole('checkbox');
        fireEvent.click(checkboxes[1]);
        expect(checkboxes[1].checked).toBe(true);

        const optimizeBtn = screen.getByRole('button', { name: /Optimize Selected/i });
        expect(optimizeBtn).not.toBeDisabled();
    });

    it('should trigger optimization on button click', async () => {
        optimizerApi.triggerOptimization.mockResolvedValue({
            message: 'Optimization started',
            task_id: 'task1'
        });

        await renderPage();

        await waitFor(() => {
            expect(screen.getByText(/hash1/i)).toBeInTheDocument();
        });

        const checkboxes = screen.getAllByRole('checkbox');
        fireEvent.click(checkboxes[1]);

        const optimizeBtn = screen.getByRole('button', { name: /Optimize Selected/i });
        fireEvent.click(optimizeBtn);

        expect(optimizerApi.triggerOptimization).toHaveBeenCalledWith(['hash1']);

        await waitFor(() => {
            expect(screen.getByText(/Optimization started/i)).toBeInTheDocument();
        });
    });

    it('should poll for status updates during optimization', async () => {
        vi.useFakeTimers();

        optimizerApi.getStatus.mockResolvedValue({
            active_tasks: 1,
            last_run: '2023-01-01T00:00:00Z',
            last_error: null
        });

        await act(async () => {
            render(
                <MemoryRouter>
                    <AdminOptimizer />
                </MemoryRouter>
            );
        });

        // Initial call on mount
        expect(optimizerApi.getStatus).toHaveBeenCalledTimes(1);

        // Advance timers by 5 seconds
        await act(async () => {
            vi.advanceTimersByTime(5000);
        });

        // Second status call should have happened
        expect(optimizerApi.getStatus).toHaveBeenCalledTimes(2);

        // Check for optimizing status indicator
        expect(screen.getByText(/Optimization in progress/i)).toBeInTheDocument();

        vi.useRealTimers();
    });
});
