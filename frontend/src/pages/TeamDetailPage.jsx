import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTeamHistory } from '../hooks/useTeamData';
import { useAuth } from '../contexts/AuthContext';
import { LoadingSpinner } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import CenteredPageLayout from '../components/layout/CenteredPageLayout';
import Card from '../components/common/Card';
import './TeamDetailPage.css';

import { getTierName } from '../utils/tierUtils';
import { getCountryCode } from '../utils/countryUtils';

function TeamDetailPage() {
  const { nodeId } = useParams();
  const { data, isLoading, error, refetch } = useTeamHistory(nodeId);
  const { user } = useAuth();

  // Show edit links to all logged-in users
  const canEdit = !!user;

  if (isLoading) {
    return (
      <CenteredPageLayout>
        <LoadingSpinner message="Loading team history..." size="lg" />
      </CenteredPageLayout>
    );
  }

  if (error) {
    return (
      <CenteredPageLayout>
        <ErrorDisplay error={error} onRetry={refetch} />
      </CenteredPageLayout>
    );
  }

  return (
    <CenteredPageLayout>
      <Card
        title={data?.current_name || "Team History"}
        subtitle={
          <div className="team-header-details">
            {data?.legal_name && <div><strong>Legal Name:</strong> {data.legal_name}</div>}
            {data?.display_name && <div><strong>Display Name:</strong> {data.display_name}</div>}
            <div className="team-dates">
              Founded: {data?.founding_year} {data?.dissolution_year ? `• Dissolved: ${data.dissolution_year}` : ''}
            </div>
          </div>
        }
      >
        <div className="team-detail-content">
          <section>
            <h3>Timeline</h3>
            {data?.timeline && data.timeline.length > 0 ? (
              <div className="timeline-list">
                {[...data.timeline].reverse().map((era, index) => (
                  <div key={index} className="timeline-era">
                    <div className="era-year">{era.year}</div>
                    <div className="era-content">
                      <div className="era-info">
                        <h4>
                          {canEdit && era.era_id ? (
                            <Link
                              to={`/maintenance/teams?nodeId=${nodeId}&eraId=${era.era_id}`}
                              className="admin-edit-link-name"
                              title="Edit this era"
                            >
                              {era.name}
                            </Link>
                          ) : (
                            era.name
                          )}
                        </h4>
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
                            {era.sponsors.map((sponsor, sIndex) => {
                              const badge = (
                                <div
                                  key={sIndex}
                                  className={`sponsor-badge ${canEdit && sponsor.master_id ? 'clickable' : ''}`}
                                  style={{
                                    backgroundColor: sponsor.color || '#ccc',
                                    borderLeft: `3px solid ${sponsor.color ? 'rgba(0,0,0,0.2)' : 'transparent'}`
                                  }}
                                >
                                  {sponsor.brand_name}
                                </div>
                              );

                              // Wrap in Link if user can edit and master_id is present
                              return canEdit && sponsor.master_id ? (
                                <Link
                                  key={sIndex}
                                  to={`/maintenance/sponsors?edit=${sponsor.master_id}`}
                                  className="sponsor-badge-link"
                                  title="Edit this sponsor"
                                >
                                  {badge}
                                </Link>
                              ) : (
                                badge
                              );
                            })}
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
      </Card>
    </CenteredPageLayout>
  );
}

export default TeamDetailPage;
