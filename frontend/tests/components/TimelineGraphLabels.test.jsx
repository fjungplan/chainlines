import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, act } from '@testing-library/react';
import TimelineGraph from '../../src/components/TimelineGraph';
import { AuthProvider } from '../../src/contexts/AuthContext';
import { BrowserRouter } from 'react-router-dom';

// Use vi.hoisted to allow access inside vi.mock factory
const { zoomHandlerMock, styleSpy } = vi.hoisted(() => ({
    zoomHandlerMock: vi.fn(),
    styleSpy: vi.fn(),
}));

// Mock D3
vi.mock('d3', () => {
    // Helper to create chainable mock
    const chainable = () => {
        const obj = {
            select: vi.fn(),
            selectAll: vi.fn(),
            append: vi.fn(),
            insert: vi.fn(),
            attr: vi.fn(),
            style: vi.fn(),
            on: vi.fn(),
            data: vi.fn(),
            join: vi.fn(),
            cx: vi.fn(),
            cy: vi.fn(),
            r: vi.fn(),
            call: vi.fn(),
            filter: vi.fn(),
            scaleExtent: vi.fn(),
            translateExtent: vi.fn(),
            remove: vi.fn(),
            empty: vi.fn(),
            node: vi.fn(),
            each: vi.fn(),
        };
        // Make them return unique objects or self to allow chaining
        Object.keys(obj).forEach(key => obj[key].mockReturnValue(obj));

        // Custom overrides for specific logic
        // Custom overrides for specific logic
        obj.style.mockImplementation(styleSpy); // Capture style calls
        obj.empty.mockReturnValue(false); // Assume elements exist

        // For enter/update/exit pattern in .join
        obj.join.mockImplementation((enter, update, exit) => {
            if (typeof enter === 'function') enter(obj);
            if (typeof update === 'function') update(obj);
            if (typeof exit === 'function') exit(obj);
            return obj;
        });

        // For .each
        obj.each.mockImplementation(function (callback) {
            const mockNode = { width: 100, height: 20 }; // dummy datum
            callback.call(obj, mockNode);
            return obj;
        });

        return obj;
    };

    const rootMock = chainable();

    // Create recursive zoomIdentity mock
    const zoomIdentityMock = {
        k: 1, x: 0, y: 0,
        translate: vi.fn(),
        scale: vi.fn(),
        toString: () => 'translate(0,0) scale(1)'
    };
    zoomIdentityMock.translate.mockReturnValue(zoomIdentityMock);
    zoomIdentityMock.scale.mockReturnValue(zoomIdentityMock);

    return {
        select: vi.fn(() => rootMock),
        selectAll: vi.fn(() => rootMock), // d3.selectAll
        zoom: vi.fn(() => ({
            scaleExtent: vi.fn().mockReturnThis(),
            translateExtent: vi.fn().mockReturnThis(),
            filter: vi.fn().mockReturnThis(),
            on: (event, handler) => {
                if (event === 'zoom') {
                    zoomHandlerMock.mockImplementation(handler);
                }
                return this; // chaining
            },
            transform: vi.fn()
        })),
        zoomIdentity: zoomIdentityMock
    };
});


// Mock child components
vi.mock('../../src/components/ControlPanel', () => ({ default: () => null }));
vi.mock('../../src/components/Tooltip', () => ({ default: () => null }));
vi.mock('../../src/utils/layoutCalculator', () => ({
    LayoutCalculator: class {
        calculateLayout() { return { nodes: [{ id: 1 }], links: [], xScale: () => 0, yearRange: { min: 2000, max: 2001 } }; }
    }
}));

// ResizeObserver mock
global.ResizeObserver = class {
    observe() { }
    unobserve() { }
    disconnect() { }
};

describe('TimelineGraph Labels', () => {
    // Setup default props
    const defaultProps = {
        data: { nodes: [{ id: 1, eras: [] }], links: [] },
        onYearRangeChange: () => { },
        onTierFilterChange: () => { },
    };

    const renderComponent = () => {
        return render(
            <AuthProvider>
                <BrowserRouter>
                    <TimelineGraph {...defaultProps} />
                </BrowserRouter>
            </AuthProvider>
        );
    };

    beforeEach(() => {
        vi.clearAllMocks();
        styleSpy.mockReturnThis(); // chainable
    });

    it('toggles label visibility based on zoom scale', async () => {
        renderComponent();

        // 1. Initial State (k=1)
        // Wait for render / effect. TimelineGraph logic runs internally.
        // We need to trigger the zoom handler to "simulate" the behavior we are testing.

        // Use fake timers to handle the 100ms throttle in zoom handler
        vi.useFakeTimers();

        // Let's filter calls to style('display', ...)
        const getDisplayCalls = () => styleSpy.mock.calls.filter(call => call[0] === 'display');

        // Clear initial calls
        styleSpy.mockClear();

        // Trigger Zoom to 0.5 (Should be VISIBLE)
        // Logic: 0.5 < 1.2 => VISIBLE
        if (zoomHandlerMock.getMockImplementation()) {
            await act(async () => {
                zoomHandlerMock.getMockImplementation()({
                    transform: { k: 0.5, x: 0, y: 0 }
                });
                vi.advanceTimersByTime(200); // Advance past throttle
            });
        }

        let lastCall = getDisplayCalls().pop();
        expect(lastCall).toBeDefined();
        // display: null means visible
        expect(lastCall[1]).toBe(null);


        // Trigger Zoom to 1.0 (Should be VISIBLE)
        if (zoomHandlerMock.getMockImplementation()) {
            await act(async () => {
                zoomHandlerMock.getMockImplementation()({
                    transform: { k: 1.0, x: 0, y: 0 }
                });
                vi.advanceTimersByTime(200);
            });
        }

        lastCall = getDisplayCalls().pop();
        expect(lastCall).toBeDefined();
        expect(lastCall[1]).toBe(null);


        // Trigger Zoom to 1.25 (Should be HIDDEN - Jersey Slices active)
        if (zoomHandlerMock.getMockImplementation()) {
            await act(async () => {
                zoomHandlerMock.getMockImplementation()({
                    transform: { k: 1.25, x: 0, y: 0 }
                });
                vi.advanceTimersByTime(200);
            });
        }

        lastCall = getDisplayCalls().pop();
        expect(lastCall).toBeDefined();
        // display: 'none' means hidden
        expect(lastCall[1]).toBe('none');

        vi.useRealTimers();
    });
});
