import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import '@testing-library/jest-dom';
import Select from '../../../src/components/common/Select';

describe('Select', () => {
    const options = [
        { value: '1', label: 'Option 1' },
        { value: '2', label: 'Option 2' },
    ];

    it('renders correctly', () => {
        render(<Select label="Test Select" name="test" options={options} />);
        expect(screen.getByLabelText('Test Select')).toBeInTheDocument();
        expect(screen.getByRole('combobox')).toBeInTheDocument();
        expect(screen.getByText('Option 1')).toBeInTheDocument();
        expect(screen.getByText('Option 2')).toBeInTheDocument();
    });

    it('handles change events', () => {
        const handleChange = vi.fn();
        render(<Select label="Test Select" name="test" options={options} onChange={handleChange} />);
        const select = screen.getByRole('combobox');
        fireEvent.change(select, { target: { value: '2' } });
        expect(handleChange).toHaveBeenCalled();
        expect(select).toHaveValue('2');
    });

    it('displays error message', () => {
        render(<Select label="Test Select" name="test" options={options} error="Invalid selection" />);
        expect(screen.getByText('Invalid selection')).toBeInTheDocument();
        expect(screen.getByRole('combobox')).toHaveClass('error');
    });
});
