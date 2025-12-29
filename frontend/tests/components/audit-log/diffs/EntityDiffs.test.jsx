import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import TeamDiff from '../../../../src/components/audit-log/diffs/TeamDiff';
import EraDiff from '../../../../src/components/audit-log/diffs/EraDiff';
import SponsorDiff from '../../../../src/components/audit-log/diffs/SponsorDiff';
import BrandDiff from '../../../../src/components/audit-log/diffs/BrandDiff';
import SponsorLinkDiff from '../../../../src/components/audit-log/diffs/SponsorLinkDiff';
import LineageDiff from '../../../../src/components/audit-log/diffs/LineageDiff';

// Mock DiffTable to verify the props passed to it
vi.mock('../../../../src/components/audit-log/DiffTable', () => ({
    default: ({ before, after }) => (
        <div data-testid="mock-diff-table">
            <div data-testid="before-keys">{Object.keys(before || {}).join(',')}</div>
            <div data-testid="after-keys">{Object.keys(after || {}).join(',')}</div>
        </div>
    )
}));

describe('Entity Diff Components', () => {
    const fullSnapshot = {
        id: 'uuid',
        created_at: '2024-01-01',
        legal_name: 'Test Team',
        display_name: 'Test Display',
        founding_year: 2000,
        dissolution_year: null,
        is_protected: false,
        registered_name: 'Registered Era',
        uci_code: 'UCI',
        country_code: 'BEL',
        tier_level: 'WT',
        valid_from: 2020,
        season_year: 2024,
        industry_sector: 'Tech',
        brand_name: 'Test Brand',
        default_hex_color: '#000000',
        era_name: 'Era Name',
        rank: 1,
        prominence: 0.5,
        hex_color_override: null,
        lineage_type: 'SPLIT',
        year: 2022,
        predecessor_names: ['Old Team'],
        successor_names: ['New Team A', 'New Team B'],
        extra_field: 'Should not appear'
    };

    describe('TeamDiff', () => {
        it('renders only team-specific fields', () => {
            render(<TeamDiff before={fullSnapshot} after={fullSnapshot} />);
            const keys = screen.getByTestId('before-keys').textContent.split(',');

            const expected = ['legal_name', 'display_name', 'founding_year', 'dissolution_year', 'is_protected'].sort();
            const actual = keys.sort();

            expect(actual).toEqual(expected);
        });
    });

    describe('EraDiff', () => {
        it('renders only era-specific fields', () => {
            render(<EraDiff before={fullSnapshot} after={fullSnapshot} />);
            const keys = screen.getByTestId('before-keys').textContent.split(',');

            const expected = ['registered_name', 'uci_code', 'country_code', 'tier_level', 'valid_from', 'season_year'].sort();
            const actual = keys.sort();

            expect(actual).toEqual(expected);
        });
    });

    describe('SponsorDiff', () => {
        it('renders only sponsor-specific fields', () => {
            render(<SponsorDiff before={fullSnapshot} after={fullSnapshot} />);
            const keys = screen.getByTestId('before-keys').textContent.split(',');

            const expected = ['legal_name', 'display_name', 'industry_sector'].sort();
            const actual = keys.sort();

            expect(actual).toEqual(expected);
        });
    });

    describe('BrandDiff', () => {
        it('renders only brand-specific fields', () => {
            render(<BrandDiff before={fullSnapshot} after={fullSnapshot} />);
            const keys = screen.getByTestId('before-keys').textContent.split(',');

            const expected = ['brand_name', 'display_name', 'default_hex_color'].sort();
            const actual = keys.sort();

            expect(actual).toEqual(expected);
        });
    });

    describe('SponsorLinkDiff', () => {
        it('renders only link-specific fields', () => {
            render(<SponsorLinkDiff before={fullSnapshot} after={fullSnapshot} />);
            const keys = screen.getByTestId('before-keys').textContent.split(',');

            const expected = ['era_name', 'brand_name', 'prominence', 'rank', 'hex_color_override'].sort();
            const actual = keys.sort();

            expect(actual).toEqual(expected);
        });
    });

    describe('LineageDiff', () => {
        it('renders only lineage-specific fields', () => {
            render(<LineageDiff before={fullSnapshot} after={fullSnapshot} />);
            const keys = screen.getByTestId('before-keys').textContent.split(',');

            const expected = ['lineage_type', 'year', 'predecessor_names', 'successor_names'].sort();
            const actual = keys.sort();

            expect(actual).toEqual(expected);
        });
    });
});
