import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import TimelineGraph from '../src/components/TimelineGraph';
import HamburgerMenu from '../src/components/layout/HamburgerMenu';
import { AuthProvider } from '../src/contexts/AuthContext';
import { BrowserRouter } from 'react-router-dom';

// Mock D3 to avoid complex SVG logic errors
vi.mock('d3', () => ({
    select: () => ({
        select: () => ({
            attr: () => ({}),
            style: () => ({}),
            empty: () => true,
            remove: () => { },
            append: () => ({
                attr: () => ({}),
                style: () => ({}),
                selectAll: () => ({
                    data: () => ({
                        join: () => ({
                            attr: () => ({}),
                            style: () => ({}),
                            on: () => ({}),
                            each: () => ({}),
                            classed: () => ({})
                        }),
                        classed: () => ({})
                    })
                })
            }),
            selectAll: () => ({
                remove: () => { },
                classed: () => ({})
            })
        }),
        selectAll: () => ({
            remove: () => { },
            classed: () => ({})
        }),
        append: () => ({
            attr: () => ({}),
            style: () => ({})
        }),
        attr: () => ({}),
        style: () => ({}),
        call: () => ({})
    }),
    zoom: () => ({
        scaleExtent: () => ({
            translateExtent: () => ({
                filter: () => ({
                    on: () => { }
                })
            })
        }),
    }),
    zoomIdentity: {
        translate: () => ({
            scale: () => ({})
        }),
        k: 1, x: 0, y: 0
    }
}));

// Mock child components
vi.mock('../src/components/ControlPanel', () => ({
    default: () => <div data-testid="control-panel">Control Panel</div>
}));

vi.mock('../src/components/NavigationHint', () => ({
    default: () => <div data-testid="nav-hint">Nav Hint</div>
}));

vi.mock('../src/components/Minimap', () => ({
    default: () => <div data-testid="minimap">Minimap</div>
}));

vi.mock('../src/utils/layoutCalculator', () => ({
    LayoutCalculator: class {
        static fetchPrecomputedLayouts() { return Promise.resolve(null); }
        constructor() { }
        calculateLayout() { return { nodes: [], links: [], xScale: () => 0, yearRange: { min: 2000, max: 2001 } }; }
    }
}));

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
    observe() { }
    unobserve() { }
    disconnect() { }
};

describe('Versioning and Navigation', () => {
    it('TimelineGraph shows version v0.9.3', () => {
        render(
            <AuthProvider>
                <BrowserRouter>
                    <TimelineGraph data={{ nodes: [], links: [] }} />
                </BrowserRouter>
            </AuthProvider>
        );
        expect(screen.getByText(/v0.9.3/i)).toBeInTheDocument();
    });

    it('HamburgerMenu shows Change Log link', async () => {
        const { container } = render(
            <BrowserRouter>
                <HamburgerMenu />
            </BrowserRouter>
        );

        // Open menu
        const button = container.querySelector('.hamburger-button');
        fireEvent.click(button);

        expect(screen.getByText(/Change Log/i)).toBeInTheDocument();
    });
});
