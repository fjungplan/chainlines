import { useState, useEffect } from 'react';
import { useTimeline } from '../hooks/useTeamData';
import { LoadingSpinner } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import TimelineGraph from '../components/TimelineGraph';
import { ResolutionBlocker } from '../components/common/ResolutionBlocker';
import './HomePage.css';

function HomePage() {
  const currentYear = new Date().getFullYear();
  const [filtersVersion, setFiltersVersion] = useState(0);
  const [fullData, setFullData] = useState(null); // State for full unfiltered data (for Minimap)

  const [filters, setFilters] = useState({
    start_year: 1900,
    end_year: currentYear,
    tier_filter: [1, 2, 3],
    focus_node_id: null
  });

  const { data, isLoading, error, refetch } = useTimeline(filters);

  // Cache full data on first successful load (initial filters are unfiltered range)
  useEffect(() => {
    if (data && !fullData && data.nodes?.length > 0) {
      setFullData(data);
      console.log('Cached full data for Minimap:', data.nodes.length, 'nodes');
    }
  }, [data, fullData]);

  const handleYearRangeChange = (startYear, endYear) => {
    setFilters(prev => ({
      ...prev,
      start_year: startYear,
      end_year: endYear
    }));
    setFiltersVersion(v => v + 1); // force downstream refresh even if values unchanged
  };

  const handleTierFilterChange = (tiers) => {
    setFilters(prev => ({
      ...prev,
      tier_filter: tiers.length > 0 ? tiers : null
    }));
  };

  const handleFocusChange = (nodeId) => {
    setFilters(prev => ({
      ...prev,
      focus_node_id: nodeId
    }));
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading timeline..." size="lg" />;
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={refetch} />;
  }

  // Calculate start/end for blocker based on FULL data range if possible, or defaults
  // Use data range (1900-2026) for blocker calculation
  const blockerStart = filters.start_year;
  const blockerEnd = filters.end_year;

  return (
    <ResolutionBlocker startYear={blockerStart} endYear={blockerEnd}>
      <TimelineGraph
        data={data}
        fullData={fullData}
        onYearRangeChange={handleYearRangeChange}
        onTierFilterChange={handleTierFilterChange}
        onFocusChange={handleFocusChange}
        filtersVersion={filtersVersion}
        initialStartYear={filters.start_year}
        initialEndYear={filters.end_year}
        currentStartYear={filters.start_year}
        currentEndYear={filters.end_year}
        initialTiers={filters.tier_filter || [1, 2, 3]}
        onEditSuccess={refetch}
      />
    </ResolutionBlocker>
  );
}

export default HomePage;
