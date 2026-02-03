import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import BrandTransferModal from '../../../src/components/maintenance/BrandTransferModal';
import { sponsorsApi } from '../../../src/api/sponsors';
import { editsApi } from '../../../src/api/edits';

// Mock APIs
vi.mock('../../../src/api/sponsors', () => ({
    sponsorsApi: {
        searchMasters: vi.fn(),
        getMaster: vi.fn(),
        deleteMaster: vi.fn()
    }
}));

vi.mock('../../../src/api/edits', () => ({
    editsApi: {
        updateSponsorBrand: vi.fn()
    }
}));

// Mock Loading
vi.mock('../../../src/components/common/Loading', () => ({
    LoadingSpinner: () => <div>Loading...</div>
}));

// Mock Auth
vi.mock('../../../src/contexts/AuthContext', () => ({
    useAuth: () => ({
        isTrusted: () => true,
        isAdmin: () => true,
        isModerator: () => false
    })
}));

describe('BrandTransferModal Cleanup', () => {
    it('should prompt to delete source sponsor when it becomes empty', async () => {
        // Setup Mocks
        const mockSourceSponsor = { master_id: 'src-123', legal_name: 'Empty Source' };
        const mockBrand = { brand_id: 'b-1', brand_name: 'Sole Brand', default_hex_color: '#000' };

        sponsorsApi.searchMasters.mockResolvedValue([mockSourceSponsor]);
        sponsorsApi.getMaster.mockResolvedValue({ ...mockSourceSponsor, brands: [mockBrand] });
        editsApi.updateSponsorBrand.mockResolvedValue({});
        sponsorsApi.deleteMaster.mockResolvedValue(true);

        // Render
        render(
            <BrandTransferModal
                isOpen={true}
                receivingMasterId="target-abc"
                receivingMasterName="Target Corp"
                onClose={() => { }}
                onSuccess={() => { }}
            />
        );

        // 1. Search Step
        const searchInput = screen.getByPlaceholderText(/type at least 2 characters/i);
        fireEvent.change(searchInput, { target: { value: 'Emp' } });

        await waitFor(() => {
            expect(screen.getByText('Empty Source')).toBeInTheDocument();
        });
        fireEvent.click(screen.getByText('Empty Source'));

        // 2. Select Step (Auto-loaded brands)
        await waitFor(() => {
            expect(screen.getByText('Sole Brand')).toBeInTheDocument();
        });

        // Select the sole brand
        fireEvent.click(screen.getByText('Sole Brand'));

        // Click Review
        fireEvent.click(screen.getByText(/review import/i));

        // 3. Confirm Step
        fireEvent.click(screen.getByText(/confirm import/i));

        // 4. Verification (TDD EXPECTATION: SHOULD FAIL HERE FIRST)
        // Expect prompt
        await waitFor(() => {
            expect(screen.getByText(/sponsor cleanup/i)).toBeInTheDocument();
        });

        // Click Yes to Delete
        fireEvent.click(screen.getByText(/yes, delete empty sponsor/i));

        // Verify API Call
        expect(sponsorsApi.deleteMaster).toHaveBeenCalledWith('src-123');
    });
});
