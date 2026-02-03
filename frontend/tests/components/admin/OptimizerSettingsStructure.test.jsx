import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import OptimizerSettings from '../../../src/pages/OptimizerSettings';
import { optimizerConfigApi } from '../../../src/api/optimizerConfig';

vi.mock('../../../src/api/optimizerConfig', () => ({
    optimizerConfigApi: {
        getConfig: vi.fn()
    }
}));

describe('OptimizerSettings Structure', () => {
    const mockConfig = {
        GROUPWISE: {
            MAX_RIGID_DELTA: 20,
            SA_MAX_ITER: 50,
            SA_INITIAL_TEMP: 100,
            SEARCH_RADIUS: 10
        },
        SCOREBOARD: { ENABLED: true },
        PASS_SCHEDULE: [],
        SEARCH_RADIUS: 50,
        TARGET_RADIUS: 10,
        WEIGHTS: {
            ATTRACTION: 1000,
            CUT_THROUGH: 10000,
            BLOCKER: 5000,
            Y_SHAPE: 500,
            LANE_SHARING: 1000,
            OVERLAP_BASE: 500000,
            OVERLAP_FACTOR: 10000
        },
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
        }
    };

    it('enforces the correct heading hierarchy', async () => {
        optimizerConfigApi.getConfig.mockResolvedValue(mockConfig);

        render(
            <MemoryRouter>
                <OptimizerSettings />
            </MemoryRouter>
        );

        // Wait for config to load
        expect(await screen.findByText(/Optimizer Settings/i)).toBeInTheDocument();

        // H1
        const mainTitle = screen.getByRole('heading', { level: 1 });
        expect(mainTitle).toHaveTextContent(/Optimizer Settings/i);

        // H2 Sections
        const sections = screen.getAllByRole('heading', { level: 2 });
        const sectionTexts = sections.map(h => h.textContent);
        expect(sectionTexts).toContain('Live Algorithm');
        expect(sectionTexts).toContain('Shared Parameters');
        expect(sectionTexts).toContain('Genetic Algorithm');

        // H3 Subsections
        const subsections = screen.getAllByRole('heading', { level: 3 });
        const subsectionTexts = subsections.map(h => h.textContent);
        expect(subsectionTexts.some(t => /Groupwise Parameters/i.test(t))).toBe(true);
        expect(subsectionTexts.some(t => /Pass Schedule/i.test(t))).toBe(true);
        expect(subsectionTexts.some(t => /Geometric Parameters/i.test(t))).toBe(true);
        expect(subsectionTexts.some(t => /Cost Weights/i.test(t))).toBe(true);
        expect(subsectionTexts.some(t => /Population Parameters/i.test(t))).toBe(true);
        expect(subsectionTexts.some(t => /Mutation Strategies/i.test(t))).toBe(true);
    });

    it('wraps sections and subsections in correct containers', async () => {
        optimizerConfigApi.getConfig.mockResolvedValue(mockConfig);

        const { container } = render(
            <MemoryRouter>
                <OptimizerSettings />
            </MemoryRouter>
        );

        await screen.findByText(/Optimizer Settings/i);

        // Sections should have .settings-section
        const sections = container.querySelectorAll('.settings-section');
        expect(sections.length).toBeGreaterThanOrEqual(3);

        // Subsections should have .settings-subsection
        const subsections = container.querySelectorAll('.settings-subsection');
        expect(subsections.length).toBeGreaterThanOrEqual(6);
    });
});
