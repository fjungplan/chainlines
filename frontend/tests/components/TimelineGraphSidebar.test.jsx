import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import '@testing-library/jest-dom';
import { render, screen, fireEvent } from '@testing-library/react';
import TimelineGraph from '../../src/components/TimelineGraph';
import { AuthProvider } from '../../src/contexts/AuthContext';
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
              each: () => ({})
            })
          })
        })
      }),
      selectAll: () => ({
        remove: () => { }
      })
    }),
    selectAll: () => ({
      remove: () => { }
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

// Mock child components to isolate Sidebar logic
vi.mock('../../src/components/ControlPanel', () => ({
  default: () => <div data-testid="control-panel">Control Panel Content</div>
}));

vi.mock('../../src/components/EditMetadataWizard', () => ({ default: () => null }));
vi.mock('../../src/components/MergeWizard', () => ({ default: () => null }));
vi.mock('../../src/components/SplitWizard', () => ({ default: () => null }));
vi.mock('../../src/components/CreateTeamWizard', () => ({ default: () => null }));
vi.mock('../../src/utils/layoutCalculator', () => ({
  LayoutCalculator: class {
    calculateLayout() { return { nodes: [], links: [], xScale: () => 0, yearRange: { min: 2000, max: 2001 } }; }
  }
}));

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() { }
  unobserve() { }
  disconnect() { }
};

describe('TimelineGraph Sidebar', () => {
  const defaultProps = {
    data: { nodes: [], links: [] },
    onYearRangeChange: () => { },
    onTierFilterChange: () => { },
  };

  const renderComponent = () => {
    // Need to wrap in Router because TimelineGraph uses useNavigate
    // Need AuthProvider because it uses useAuth
    return render(
      <AuthProvider>
        <BrowserRouter>
          <TimelineGraph {...defaultProps} />
        </BrowserRouter>
      </AuthProvider>
    );
  };

  it('renders sidebar collapsed by default', () => {
    renderComponent();
    // Sidebar should be collapsed initially
    const sidebar = screen.getByTestId('control-panel').closest('.timeline-sidebar');
    expect(sidebar).toHaveClass('collapsed');
  });

  it('expands sidebar when toggle button is clicked', async () => {
    renderComponent();

    // Find the expand button (which should be visible when collapsed)
    // We'll assume the same button toggles, or specifically look for "expand"
    const toggleButton = screen.getByLabelText(/expand sidebar/i);
    fireEvent.click(toggleButton);

    const sidebar = screen.getByTestId('control-panel').closest('.timeline-sidebar');
    expect(sidebar).not.toHaveClass('collapsed');
  });
});
