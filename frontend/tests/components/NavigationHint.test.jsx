import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import NavigationHint from '../../src/components/NavigationHint';

describe('NavigationHint', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.runOnlyPendingTimers();
        vi.useRealTimers();
    });

    it('renders instruction text correctly', () => {
        render(<NavigationHint />);
        screen.debug();
        expect(screen.getByText(/Ctrl \+ Scroll/i)).toBeInTheDocument();
        expect(screen.getByText(/Middle Click/i)).toBeInTheDocument();
    });

    it('disappears after timeout', () => {
        render(<NavigationHint duration={3000} />);

        expect(screen.getByRole('presentation')).toBeVisible();

        act(() => {
            vi.advanceTimersByTime(3100);
        });

        // re-render should have happened
        expect(screen.queryByRole('presentation')).not.toBeInTheDocument();
    });

    it('disappears immediately on click/dismiss', () => {
        render(<NavigationHint />);
        const hint = screen.getByRole('presentation');

        act(() => {
            fireEvent.click(hint);
        });

        expect(screen.queryByRole('presentation')).not.toBeInTheDocument();
    });
});
