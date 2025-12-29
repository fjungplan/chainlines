import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import DiffTable from '../../../src/components/audit-log/DiffTable';

describe('DiffTable', () => {
    it('renders all unique keys', () => {
        const before = { a: 1, b: 2 };
        const after = { b: 3, c: 4 };
        const { container } = render(<DiffTable before={before} after={after} />);

        expect(screen.getByText('a')).toBeInTheDocument();
        expect(screen.getByText('b')).toBeInTheDocument();
        expect(screen.getByText('c')).toBeInTheDocument();

        // 3 rows + header
        const rows = container.querySelectorAll('tbody tr');
        expect(rows).toHaveLength(3);
    });

    it('highlights changed values', () => {
        const before = { a: 1, b: 2 };
        const after = { a: 1, b: 3 }; // b changed
        const { container } = render(<DiffTable before={before} after={after} />);

        const rows = container.querySelectorAll('tbody tr');
        // Row 'a' (index 0 or 1 depending on sort, keys sorted: a, b)
        // a: before=1, after=1 -> No highlight
        // b: before=2, after=3 -> Highlight

        // Since sorted, row 0 is a, row 1 is b.
        expect(rows[0]).not.toHaveClass('diff-row-changed');
        expect(rows[1]).toHaveClass('diff-row-changed');
    });

    it('renders primitive values correctly', () => {
        const before = { bool: true, str: 'text', num: 123, nullVal: null };
        const after = { bool: false, str: 'text', num: 123, nullVal: undefined };

        render(<DiffTable before={before} after={after} />);

        expect(screen.getByText('true')).toBeInTheDocument();
        expect(screen.getByText('false')).toBeInTheDocument();
        expect(screen.getAllByText('text')).toHaveLength(2);
        expect(screen.getAllByText('123')).toHaveLength(2);

        // Null/undefined render as '-'
        const dashes = screen.getAllByText('-');
        expect(dashes).toHaveLength(2); // One for nullVal before (Wait, null renders -?), one for undefined after
    });

    it('renders objects as JSON', () => {
        const before = { obj: { x: 1 } };
        const after = { obj: { x: 2 } };

        const { container } = render(<DiffTable before={before} after={after} />);

        // Check for JSON text content
        // Simple regex check or string match
        expect(screen.getByText(/"x": 1/)).toBeInTheDocument();
        expect(screen.getByText(/"x": 2/)).toBeInTheDocument();
    });

    it('handles empty input', () => {
        render(<DiffTable before={null} after={null} />);
        expect(screen.getByText('No data to compare.')).toBeInTheDocument();
    });
});
