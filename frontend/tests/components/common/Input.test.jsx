import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import '@testing-library/jest-dom';
import Input from '../../../src/components/common/Input';

describe('Input', () => {
    it('renders correctly', () => {
        render(<Input label="Test Input" name="test" />);
        expect(screen.getByLabelText('Test Input')).toBeInTheDocument();
        expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('handles change events', () => {
        const handleChange = vi.fn();
        render(<Input label="Test Input" name="test" onChange={handleChange} />);
        const input = screen.getByRole('textbox');
        fireEvent.change(input, { target: { value: 'new value' } });
        expect(handleChange).toHaveBeenCalled();
        expect(input).toHaveValue('new value');
    });

    it('displays error message', () => {
        render(<Input label="Test Input" name="test" error="Invalid input" />);
        expect(screen.getByText('Invalid input')).toBeInTheDocument();
        expect(screen.getByRole('textbox')).toHaveClass('error');
    });

    it('renders textarea', () => {
        render(<Input label="Test Area" name="test-area" type="textarea" />);
        expect(screen.getByLabelText('Test Area')).toBeInTheDocument();
        expect(screen.getByRole('textbox')).toHaveAttribute('name', 'test-area');
        expect(screen.getByRole('textbox').tagName).toBe('TEXTAREA');
    });
});
