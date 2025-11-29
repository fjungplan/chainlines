import { useTimeline } from '../hooks/useTeamData';
import { useResponsive } from '../hooks/useResponsive';
import { LoadingSpinner } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import TimelineGraph from '../components/TimelineGraph';
import './HomePage.css';

function HomePage() {
  const { isMobile } = useResponsive();
  const { data, isLoading, error, refetch } = useTimeline({
    start_year: 2020,
    end_year: 2024,
  });

  if (isLoading) {
    return <LoadingSpinner message="Loading timeline..." size="lg" />;
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={refetch} />;
  }

  return isMobile ? (
    <div className="home-page">
      <h2>Mobile View</h2>
      <p>Mobile list view coming soon...</p>
      <div className="data-summary">
        <div className="summary-card">
          <h3>Nodes</h3>
          <p className="summary-value">{data?.nodes?.length || 0}</p>
        </div>
        <div className="summary-card">
          <h3>Links</h3>
          <p className="summary-value">{data?.links?.length || 0}</p>
        </div>
      </div>
    </div>
  ) : (
    <TimelineGraph data={data} />
  );
}

export default HomePage;
