import { useParams } from 'react-router-dom';
import { useTeamHistory } from '../hooks/useTeamData';
import { LoadingSpinner } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import './TeamDetailPage.css';

import { getTierName } from '../utils/tierUtils';
import { getCountryCode } from '../utils/countryUtils';

function TeamDetailPage() {
  const { nodeId } = useParams();
  const { data, isLoading, error, refetch } = useTeamHistory(nodeId);

  if (isLoading) {
    return <LoadingSpinner message="Loading team history..." size="lg" />;
  }

  if (error) {
    return <ErrorDisplay error={error} onRetry={refetch} />;
  }

  return (
    <div className="team-detail-page">
      <div className="team-detail-container">
        <h1>Team History</h1>

        <section>
          <h2>Overview</h2>
          <div className="team-overview">
            <p><strong>Founded:</strong> {data?.founding_year}</p>
            {data?.dissolution_year && (
              <p><strong>Dissolved:</strong> {data?.dissolution_year}</p>
            )}
          </div>
        </section>

        <section>
          <h2>Timeline</h2>
          {data?.timeline && data.timeline.length > 0 ? (
            <div className="timeline-list">
              {data.timeline.map((era, index) => (
                <div key={index} className="timeline-era">
                  <div className="era-year">{era.year}</div>
                  <div className="era-content">
                    <div className="era-info">
                      <h4>{era.name}</h4>
                      <div className="era-meta-pills">
                        {(() => {
                          const cCode = getCountryCode(era.country_code);
                          return cCode ? (
                            <span
                              className={`meta-pill flag-pill fi fi-${cCode}`}
                              title={`License: ${era.country_code}`}
                            />
                          ) : (
                            <span className="meta-pill flag-placeholder" title="Unknown Country"></span>
                          );
                        })()}
                        {era.uci_code && <span className="meta-pill uci">{era.uci_code}</span>}
                        {era.tier && (
                          <span className={`meta-pill tier tier-${era.tier}`} title={`Tier ${era.tier}`}>
                            {getTierName(era.tier, era.year)}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="era-sponsors-container">
                      {era.sponsors && era.sponsors.length > 0 && (
                        <div className="era-sponsors">
                          {era.sponsors.map((sponsor, sIndex) => (
                            <div
                              key={sIndex}
                              className="sponsor-badge"
                              style={{
                                backgroundColor: sponsor.color || '#ccc',
                                borderLeft: `3px solid ${sponsor.color ? 'rgba(0,0,0,0.2)' : 'transparent'}`
                              }}
                            >
                              {sponsor.brand_name}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p>No timeline data available.</p>
          )}
        </section>

        <section>
          <details className="data-preview">
            <summary>View Raw Data</summary>
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </details>
        </section>
      </div>
    </div>
  );
}

export default TeamDetailPage;
