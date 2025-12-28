import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import '@testing-library/jest-dom';
import Card from '../../../src/components/common/Card';

describe('Card Component', () => {
    it('renders children correctly', () => {
        render(
            <Card>
                <p>Card Content</p>
            </Card>
        );
        expect(screen.getByText('Card Content')).toBeInTheDocument();
    });

    it('renders title when provided', () => {
        render(<Card title="My Card Title">Content</Card>);
        expect(screen.getByText('My Card Title')).toBeInTheDocument();
    });

    it('renders subtitle when provided', () => {
        render(<Card subtitle="Card Subtitle">Content</Card>);
        expect(screen.getByText('Card Subtitle')).toBeInTheDocument();
    });

    it('applies custom className', () => {
        const { container } = render(<Card className="custom-class">Content</Card>);
        expect(container.firstChild).toHaveClass('custom-class');
    });

    it('renders header actions if provided', () => {
        render(
            <Card title="Card with Actions" headerActions={<button>Action</button>}>
                Content
            </Card>
        );
        expect(screen.getByText('Action')).toBeInTheDocument();
    });
});
