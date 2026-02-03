import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import BrandMergeModal from '../../../src/components/maintenance/BrandMergeModal';
import { sponsorsApi } from '../../../src/api/sponsors';
import { useAuth } from '../../../src/contexts/AuthContext';

// Mocks
vi.mock('../../../src/api/sponsors');
vi.mock('../../../src/contexts/AuthContext');

describe('BrandMergeModal', () => {
    const mockOnClose = vi.fn();
    const mockOnSuccess = vi.fn();

    // Test Data
    const sourceBrand = {
        brand_id: 'src-brand-1',
        brand_name: 'Source Brand',
        master_id: 'src-master-1'
    };

    const targetBrands = [
        {
            brand_id: 'target-1',
            brand_name: 'Target Brand A',
            master_id: 'target-master-1',
            default_hex_color: '#ff0000'
        }
    ];

    beforeEach(() => {
        vi.clearAllMocks();
        // Default Auth: Admin
        useAuth.mockReturnValue({
            isTrusted: () => true,
            isAdmin: () => true,
            isModerator: () => false
        });
    });

    it('should not render when not open', () => {
        render(<BrandMergeModal isOpen={false} sourceBrand={sourceBrand} onClose={mockOnClose} />);
        expect(screen.queryByText(/merge brand/i)).not.toBeInTheDocument();
    });

    it('should verify merge flow: search -> select -> confirm', async () => {
        // 1. Setup Search Mock
        sponsorsApi.searchBrands.mockResolvedValue({ items: targetBrands });
        sponsorsApi.mergeBrand.mockResolvedValue({ success: true });

        render(
            <BrandMergeModal
                isOpen={true}
                sourceBrand={sourceBrand}
                onClose={mockOnClose}
                onSuccess={mockOnSuccess}
            />
        );

        // 2. Initial State: Search Input Present
        expect(screen.getByPlaceholderText(/search brands/i)).toBeInTheDocument();
        // Use getAll because it matches the description logic if split
        expect(screen.getAllByText(/source brand/i).length).toBeGreaterThan(0);

        // 3. Perform Search
        const searchInput = screen.getByPlaceholderText(/search brands/i);
        fireEvent.change(searchInput, { target: { value: 'Target' } });

        // Wait for results
        await waitFor(() => {
            expect(sponsorsApi.searchBrands).toHaveBeenCalledWith('Target', expect.any(Number));
            expect(screen.getByText('Target Brand A')).toBeInTheDocument();
        });

        // 4. Select Target - Click the container
        const item = screen.getByText('Target Brand A').closest('.brand-item');
        fireEvent.click(item);

        // 5. Verify Confirmation Step
        // Should show "Merge [Source] into [Target]?"
        await waitFor(() => {
            expect(screen.getByRole('heading', { name: /confirm merge/i })).toBeInTheDocument();
        });

        const confirmBtn = screen.getByRole('button', { name: /confirm merge/i });
        const reasonInput = screen.getByLabelText(/justification/i);

        // 6. Verification: Button should be disabled until reason is provided
        expect(confirmBtn).toBeDisabled();

        fireEvent.change(reasonInput, { target: { value: 'Valid reason for merge' } });
        expect(confirmBtn).not.toBeDisabled();

        // 7. Click Confirm
        fireEvent.click(confirmBtn);

        // 8. Verify API Call
        await waitFor(() => {
            expect(sponsorsApi.mergeBrand).toHaveBeenCalledWith(sourceBrand.brand_id, 'target-1', 'Valid reason for merge');
            expect(mockOnSuccess).toHaveBeenCalled();
            expect(mockOnClose).toHaveBeenCalled();
        });
    });

    it('should prevent merging into itself', async () => {
        // If search returns the source brand itself, it should be filtered or disabled
        sponsorsApi.searchBrands.mockResolvedValue({ items: [sourceBrand] });

        const { container } = render(
            <BrandMergeModal
                isOpen={true}
                sourceBrand={sourceBrand}
                onClose={mockOnClose}
            />
        );

        fireEvent.change(screen.getByPlaceholderText(/search brands/i), { target: { value: 'Source' } });

        await waitFor(() => {
            // It should call search
            expect(sponsorsApi.searchBrands).toHaveBeenCalled();

            // Check that NO .brand-item elements exist in the DOM
            const items = container.querySelectorAll('.brand-item');
            expect(items.length).toBe(0);
        });
    });
});
