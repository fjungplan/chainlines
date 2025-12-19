import { useState, useEffect } from 'react';
import { teamsApi } from '../../api/teams';
import { LoadingSpinner } from '../Loading';

export default function TeamEraBubbles({ nodeId, onEraSelect, onCreateEra }) {
    const [eras, setEras] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (nodeId) {
            loadEras();
        } else {
            setEras([]);
            setLoading(false);
        }
    }, [nodeId]);

    const loadEras = async () => {
        setLoading(true);
        setError(null);
        try {
            // Get all eras (no filter)
            const data = await teamsApi.getTeamEras(nodeId);
            setEras(data);
        } catch (err) {
            console.error(err);
            setError("Failed to load eras");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingSpinner message="Loading eras..." />;

    return (
        <div className="era-bubbles-container">


            {error && <div className="error-text">{error}</div>}

            {!nodeId ? (
                <div className="empty-text">Save team to add eras.</div>
            ) : eras.length === 0 ? (
                <div className="empty-text">No eras recorded.</div>
            ) : (
                <div className="bubbles-list">
                    {eras.map(era => (
                        <div
                            key={era.era_id}
                            className={`era-bubble tier-${era.tier_level || 3}`}
                            onClick={() => onEraSelect(era.era_id)}
                        >
                            <span className="era-year">{era.season_year}</span>
                            <span className="era-name">{era.registered_name}</span>
                            {era.uci_code && <span className="era-code">{era.uci_code}</span>}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
