import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import NotificationBadge from '../../../src/components/common/NotificationBadge';

describe('NotificationBadge', () => {
    it('does not render when count is 0', () => {
        const { container } = render(<NotificationBadge count={0} />);
        expect(container).toBeEmptyDOMElement();
    });

    it('does not render when count is null or undefined', () => {
        const { container: containerNull } = render(<NotificationBadge count={null} />);
        expect(containerNull).toBeEmptyDOMElement();

        const { container: containerUndefined } = render(<NotificationBadge />);
        expect(containerUndefined).toBeEmptyDOMElement();
    });

    it('renders count when greater than 0', () => {
        render(<NotificationBadge count={5} />);
        expect(screen.getByText('5')).toBeInTheDocument();
        expect(screen.getByText('5')).toHaveClass('notification-badge');
    });

    it('renders large numbers correctly', () => {
        render(<NotificationBadge count={99} />);
        expect(screen.getByText('99')).toBeInTheDocument();
    });
});
