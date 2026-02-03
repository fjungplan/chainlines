import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import SponsorMasterEditor from '../../../src/components/maintenance/SponsorMasterEditor';
import { sponsorsApi } from '../../../src/api/sponsors';
import { useAuth } from '../../../src/contexts/AuthContext';

// Mock APIs
vi.mock('../../../src/api/sponsors', () => ({
    sponsorsApi: {
        getMaster: vi.fn(),
        searchMasters: vi.fn(),
        getAllMasters: vi.fn()
    }
}));

vi.mock('../../../src/api/edits', () => ({
    editsApi: {
        createPendingEdit: vi.fn()
    }
}));

// Mock Auth Context
vi.mock('../../../src/contexts/AuthContext', () => ({
    useAuth: vi.fn()
}));

// Mock Lucide icons
vi.mock('lucide-react', () => ({
    Merge: (props) => <svg data-testid="merge-icon" {...props} />,
    ArrowLeft: () => <svg data-testid="arrow-left-icon" />,
    Save: () => <svg data-testid="save-icon" />,
    X: () => <svg data-testid="x-icon" />,
    Plus: () => <svg data-testid="plus-icon" />,
    Trash2: () => <svg data-testid="trash-icon" />,
    Repeat: () => <svg data-testid="repeat-icon" />,
    GitPullRequest: () => <svg data-testid="git-pull-request-icon" />,
    ChevronDown: () => <svg data-testid="chevron-down-icon" />,
    Search: () => <svg data-testid="search-icon" />
}));

describe('SponsorMasterEditor - Brand Merge UI', () => {
    const mockUser = { id: 'u1', role: 'admin' };
    const mockMaster = {
        master_id: 'm1',
        legal_name: 'Test Sponsor',
        brands: [
            { brand_id: 'b1', brand_name: 'Brand A', default_hex_color: '#FF0000' },
            { brand_id: 'b2', brand_name: 'Brand B', default_hex_color: '#00FF00' }
        ]
    };

    beforeEach(() => {
        vi.clearAllMocks();
        useAuth.mockReturnValue({
            user: mockUser,
            isAdmin: () => true,
            isModerator: () => false,
            isTrusted: () => true
        });
        sponsorsApi.getMaster.mockResolvedValue(mockMaster);
    });

    it('renders the merge button for each brand item correctly', async () => {
        render(<SponsorMasterEditor masterId="m1" onClose={() => { }} />);

        // Wait for brands to load
        await waitFor(() => expect(screen.getByText('Brand A')).toBeInTheDocument());

        // Find all merge buttons
        const mergeButtons = screen.getAllByTitle(/merge into another brand/i);
        expect(mergeButtons).toHaveLength(2);

        // ---------------------------------------------------------
        // TDD EXPECTATIONS (Expected to fail)
        // ---------------------------------------------------------

        // 1. Check if it's using the standard Button component with specific variant
        // Standard Button has 'btn' class
        expect(mergeButtons[0]).toHaveClass('btn');
        expect(mergeButtons[0]).toHaveClass('btn-ghost');
        expect(mergeButtons[0]).toHaveClass('btn-sm');

        // 2. Check if it's a direct child of brand-item (pushed to right)
        const brandItem = screen.getByText('Brand A').closest('.brand-item');
        expect(mergeButtons[0].parentElement).toBe(brandItem);

        // 3. Check for the Lucide Merge icon with 90deg rotation
        const mergeIcon = within(mergeButtons[0]).getByTestId('merge-icon');
        expect(mergeIcon).toHaveStyle('transform: rotate(90deg)');
    });
});
