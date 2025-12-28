import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import '@testing-library/jest-dom';
import Button from '../../../src/components/common/Button';

describe('Button Component', () => {
    it('renders children correctly', () => {
        render(<Button>Click Me</Button>);
        expect(screen.getByText('Click Me')).toBeInTheDocument();
    });

    it('handles onClick events', () => {
        const handleClick = vi.fn();
        render(<Button onClick={handleClick}>Click Me</Button>);
        fireEvent.click(screen.getByText('Click Me'));
        expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('applies variant classes correctly', () => {
        const variants = ['primary', 'secondary', 'danger', 'success', 'outline', 'ghost', 'icon'];

        variants.forEach(variant => {
            const { unmount } = render(<Button variant={variant}>Test</Button>);
            const btn = screen.getByText('Test');
            expect(btn).toHaveClass(`btn-${variant}`);
            unmount();
        });
    });

    it('applies size classes correctly', () => {
        const { rerender } = render(<Button size="sm">Small</Button>);
        expect(screen.getByText('Small')).toHaveClass('btn-sm');

        rerender(<Button size="lg">Large</Button>);
        expect(screen.getByText('Large')).toHaveClass('btn-lg');
    });

    it('applies active class when active prop is true', () => {
        render(<Button active>Active</Button>);
        expect(screen.getByText('Active')).toHaveClass('active');
    });

    it('disables the button when disabled prop is set', () => {
        const handleClick = vi.fn();
        render(<Button disabled onClick={handleClick}>Disabled</Button>);

        const btn = screen.getByText('Disabled');
        expect(btn).toBeDisabled();

        fireEvent.click(btn);
        expect(handleClick).not.toHaveBeenCalled();
    });

    it('renders as a submit button when type="submit"', () => {
        render(<Button type="submit">Submit</Button>);
        expect(screen.getByText('Submit')).toHaveAttribute('type', 'submit');
    });
});
