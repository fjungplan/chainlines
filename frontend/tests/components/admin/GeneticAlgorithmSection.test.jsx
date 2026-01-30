import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import GeneticAlgorithmSection from '../../../src/components/admin/GeneticAlgorithmSection';

describe('GeneticAlgorithmSection', () => {
    const mockConfig = {
        GENETIC_ALGORITHM: {
            POP_SIZE: 1000,
            GENERATIONS: 5000,
            MUTATION_RATE: 0.2,
            TOURNAMENT_SIZE: 10,
            TIMEOUT_SECONDS: 3600,
            PATIENCE: 500
        },
        MUTATION_STRATEGIES: {
            SWAP: 0.2,
            HEURISTIC: 0.2,
            COMPACTION: 0.3,
            EXPLORATION: 0.3
        },
        SCOREBOARD: {
            ENABLED: true
        }
    };

    it('renders all GA parameters', () => {
        render(
            <GeneticAlgorithmSection
                config={mockConfig}
                onChange={() => { }}
                onError={() => { }}
            />
        );

        expect(screen.getByLabelText(/Population Size/i)).toHaveValue(1000);
        expect(screen.getAllByLabelText(/Generations/i)[0]).toHaveValue(5000);
        expect(screen.getByLabelText(/Patience \(generations\)/i)).toHaveValue(500);
        expect(screen.getByLabelText(/Timeout \(seconds\)/i)).toHaveValue(3600);
        expect(screen.getByLabelText(/Mutation Rate/i)).toHaveValue('0.2');
        expect(screen.getByLabelText(/Tournament Size/i)).toHaveValue('10');
    });

    it('renders all mutation strategy sliders', () => {
        render(
            <GeneticAlgorithmSection
                config={mockConfig}
                onChange={() => { }}
                onError={() => { }}
            />
        );

        expect(screen.getByLabelText(/Swap probability/i)).toHaveValue('0.2');
        expect(screen.getByLabelText(/Heuristic probability/i)).toHaveValue('0.2');
        expect(screen.getByLabelText(/Compaction probability/i)).toHaveValue('0.3');
        expect(screen.getByLabelText(/Exploration probability/i)).toHaveValue('0.3');
    });

    it('renders scoreboard toggle', () => {
        render(
            <GeneticAlgorithmSection
                config={mockConfig}
                onChange={() => { }}
                onError={() => { }}
            />
        );

        const toggle = screen.getByRole('checkbox', { name: /Enable Scoreboard/i });
        expect(toggle).toBeChecked();
    });

    it('displays total sum correctly', () => {
        render(
            <GeneticAlgorithmSection
                config={mockConfig}
                onChange={() => { }}
                onError={() => { }}
            />
        );

        const statusDiv = screen.getByTestId('validation-status');
        expect(statusDiv).toHaveTextContent('Total Probability: 1.00');
        expect(statusDiv).toHaveClass('valid');
    });

    it('shows error when sum is not 1.0', () => {
        const invalidConfig = {
            ...mockConfig,
            MUTATION_STRATEGIES: {
                ...mockConfig.MUTATION_STRATEGIES,
                SWAP: 0.5 // Total becomes 1.3
            }
        };

        render(
            <GeneticAlgorithmSection
                config={invalidConfig}
                onChange={() => { }}
                onError={() => { }}
            />
        );

        const statusDiv = screen.getByTestId('validation-status');
        expect(statusDiv).toHaveTextContent('Total Probability: 1.30');
        expect(statusDiv).toHaveClass('invalid');
        expect(screen.getByText(/Must sum to 1.0/i)).toBeInTheDocument();
    });

    it('calls onError when sum becomes invalid', () => {
        const handleError = vi.fn();
        const handleChange = vi.fn();

        const { rerender } = render(
            <GeneticAlgorithmSection
                config={mockConfig}
                onChange={handleChange}
                onError={handleError}
            />
        );

        // Initial render: valid
        expect(handleError).toHaveBeenCalledWith(false); // No error

        // Update with invalid config
        const invalidConfig = {
            ...mockConfig,
            MUTATION_STRATEGIES: {
                ...mockConfig.MUTATION_STRATEGIES,
                SWAP: 0.5
            }
        };

        rerender(
            <GeneticAlgorithmSection
                config={invalidConfig}
                onChange={handleChange}
                onError={handleError}
            />
        );

        expect(handleError).toHaveBeenCalledWith(true); // Error present
    });

    it('calls onChange when scoreboard toggle changes', () => {
        const handleChange = vi.fn();
        render(
            <GeneticAlgorithmSection
                config={mockConfig}
                onChange={handleChange}
                onError={() => { }}
            />
        );

        const toggle = screen.getByRole('checkbox', { name: /Enable Scoreboard/i });
        fireEvent.click(toggle);

        expect(handleChange).toHaveBeenCalled();
        const updatedConfig = handleChange.mock.calls[0][0];
        expect(updatedConfig.SCOREBOARD.ENABLED).toBe(false);
    });
});
