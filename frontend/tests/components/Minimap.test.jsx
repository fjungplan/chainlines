import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import Minimap from '../../src/components/Minimap';
import * as d3 from 'd3';

// Mock D3
const chainable = {
    attr: vi.fn(function () { return this; }),
    call: vi.fn(function () { return this; }),
    selectAll: vi.fn(function () { return this; }),
    select: vi.fn(function () { return this; }),
    data: vi.fn(function () { return this; }),
    join: vi.fn(function () { return this; }),
    enter: vi.fn(function () { return this; }),
    append: vi.fn(function () { return this; }),
    remove: vi.fn(function () { return this; }),
    classed: vi.fn(function () { return this; }),
    on: vi.fn(function () { return this; }),
    node: () => ({}),
    filter: vi.fn(function () { return this; }),
    scale: vi.fn(function () { return this; }),
    translate: vi.fn(function () { return this; }),
};

vi.mock('d3', async () => {
    const actual = await vi.importActual('d3');
    return {
        ...actual,
        zoom: () => ({
            scaleExtent: () => ({
                translateExtent: () => ({
                    filter: () => ({
                        on: () => { },
                        transform: () => { }
                    })
                })
            })
        }),
        drag: () => ({
            on: () => chainable
        }),
        select: () => chainable,
        selectAll: () => chainable,
        zoomIdentity: {
            translate: () => ({ scale: () => ({}) })
        }
    };
});

describe('Minimap Component', () => {
    const mockLayout = {
        nodes: [
            { id: '1', x: 0, y: 0, width: 20, height: 20 },
            { id: '2', x: 2000, y: 1000, width: 20, height: 20 }
        ],
        yearRange: { min: 2000, max: 2020 },
        xScale: (val) => (val - 2000) * 100
    };

    const mockContainerDims = { width: 1000, height: 600 };
    const mockTransform = { k: 1, x: 0, y: 0 };
    const mockOnNavigate = vi.fn();

    const mockMainLayout = {
        nodes: [],
        yearRange: { min: 2005, max: 2015 },
        xScale: (val) => (val - 2005) * 50,
        rowHeight: 20
    };

    beforeEach(() => {
        vi.clearAllMocks();

        // Global ResizeObserver Mock
        global.ResizeObserver = class ResizeObserver {
            constructor(cb) {
                this.cb = cb;
            }
            observe() {
                // Trigger immediately with mock size
                this.cb([{ contentRect: { width: 200, height: 200 } }]);
            }
            disconnect() { }
        };
    });

    it('renders without crashing', () => {
        render(
            <Minimap
                layout={mockLayout}
                mainLayout={mockMainLayout}
                transform={mockTransform}
                containerDimensions={mockContainerDims}
                onNavigate={mockOnNavigate}
            />
        );
        expect(screen.getByTestId('minimap-svg')).toBeTruthy();
    });

    it('calculates dimensions based on container (fit-to-view)', async () => {
        // Simulate container dimensions on HTMLElement
        Object.defineProperty(HTMLElement.prototype, 'clientWidth', { configurable: true, value: 200 });
        Object.defineProperty(HTMLElement.prototype, 'clientHeight', { configurable: true, value: 500 }); // Distorted height

        // Mock ResizeObserver to match
        global.ResizeObserver = class ResizeObserver {
            constructor(cb) {
                this.cb = cb;
            }
            observe() {
                this.cb([{ contentRect: { width: 200, height: 500 } }]);
            }
            disconnect() { }
        };

        render(
            <Minimap
                layout={mockLayout}
                mainLayout={mockMainLayout}
                transform={mockTransform}
                containerDimensions={mockContainerDims}
                onNavigate={mockOnNavigate}
            />
        );

        // Wait for D3 interactions
        await waitFor(() => {
            const mockSelection = d3.select();
            expect(mockSelection.attr).toHaveBeenCalledWith('width', 200);
            expect(mockSelection.attr).toHaveBeenCalledWith('height', 500); // Should force height
        });

        // We don't check aspect ratio preservation anymore because it's explicitly distorted
    });
});
