import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect } from 'vitest';
import SponsorManagerModal from '../../../src/components/maintenance/SponsorManagerModal';
import { sponsorsApi } from '../../../src/api/sponsors';

// Mock API
vi.mock('../../../src/api/sponsors', () => ({
    sponsorsApi: {
        getEraLinks: vi.fn(),
        searchBrands: vi.fn(),
        replaceEraLinks: vi.fn()
    }
}));

// Mock child components to simplify testing
vi.mock('../../../src/components/Loading', () => ({
    LoadingSpinner: () => <div>Loading...</div>
}));

describe('SponsorManagerModal', () => {
    const mockLinks = [
        {
            link_id: 'l1',
            rank_order: 1,
            prominence_percent: 50,
            hex_color_override: '#FF0000', // Explicit override
            brand: {
                brand_id: 'b1',
                brand_name: 'Test Brand',
                default_hex_color: '#000000' // Default
            }
        }
    ];

    it('resets color override to default when reset button is clicked', async () => {
        sponsorsApi.getEraLinks.mockResolvedValue(mockLinks);

        render(
            <SponsorManagerModal
                isOpen={true}
                eraId="era1"
                seasonYear={2024}
                onClose={() => { }}
            />
        );

        // Wait for load
        await waitFor(() => expect(screen.getByText('Test Brand')).toBeInTheDocument());

        // Click the row to start editing
        const row = screen.getByText('Test Brand').closest('tr');
        fireEvent.click(row);

        // Verify currently displaying the override #FF0000
        // The text input for color is found by value
        const colorInput = screen.getByDisplayValue('#FF0000');
        expect(colorInput).toBeInTheDocument();

        // ---------------------------------------------------------
        // TDD STEP: Find the Reset Button (Expect failure here first)
        // ---------------------------------------------------------
        const resetBtn = screen.getByRole('button', { name: /reset to brand default/i });
        fireEvent.click(resetBtn);

        // Verify it reverted to default #000000 (check text input specifically)
        const textInput = screen.getByPlaceholderText('#RRGGBB');
        expect(textInput).toHaveValue('#000000');
    });
});
