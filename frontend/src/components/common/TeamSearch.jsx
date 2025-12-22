import { useState, useEffect, useRef } from 'react';
import { teamsApi } from '../../api/teams';
import { LoadingSpinner } from '../Loading';

/**
 * TeamSearch component for finding and selecting teams (nodes).
 * 
 * @param {Object} props
 * @param {Function} props.onSelect - Callback receiving the selected team object
 * @param {string} [props.label="Search Team"] - Input label
 * @param {string} [props.placeholder="Type to search..."] - Input placeholder
 * @param {Array<string>} [props.excludeIds=[]] - IDs to exclude from results
 * @param {Object} [props.initialSelection=null] - Initial team object to display
 */
export default function TeamSearch({
    onSelect,
    label = "Search Team",
    placeholder = "Type to search (e.g. Soudal, Visma)...",
    excludeIds = [],
    initialSelection = null
}) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);
    const [selectedTeam, setSelectedTeam] = useState(initialSelection);

    // Reset query when selection changes externally
    useEffect(() => {
        if (initialSelection) {
            setSelectedTeam(initialSelection);
        } else {
            setSelectedTeam(null);
        }
    }, [initialSelection]);

    // Search effect
    useEffect(() => {
        const fetchTeams = async () => {
            if (!query || query.length < 2) {
                setResults([]);
                return;
            }

            setIsLoading(true);
            try {
                // Determine if we are searching nodes or using a generic search
                // Use listTeams with search query
                const response = await teamsApi.listTeams({
                    search: query,
                    limit: 10
                });

                // Filter out excluded IDs
                const filtered = response.items.filter(t => !excludeIds.includes(t.node_id));
                setResults(filtered);
                setIsOpen(true);
            } catch (error) {
                console.error("Team search failed", error);
            } finally {
                setIsLoading(false);
            }
        };

        const timeoutId = setTimeout(fetchTeams, 300);
        return () => clearTimeout(timeoutId);
    }, [query, excludeIds]);

    const handleSelect = (team) => {
        setSelectedTeam(team);
        setIsOpen(false);
        setQuery('');
        onSelect(team);
    };

    const handleClear = () => {
        setSelectedTeam(null);
        onSelect(null);
    };

    return (
        <div className="team-search-container" style={{ position: 'relative', marginBottom: '1rem' }}>
            <label className="form-label">{label}</label>

            {selectedTeam ? (
                <div className="selected-team-card" style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.75rem',
                    border: '1px solid #e0e0e0',
                    borderRadius: '4px',
                    backgroundColor: '#f8f9fa'
                }}>
                    <div>
                        <strong>{selectedTeam.legal_name}</strong>
                        {selectedTeam.display_name && (
                            <div style={{ fontSize: '0.85rem', color: '#666' }}>
                                Found as: {selectedTeam.display_name}
                            </div>
                        )}
                    </div>
                    <button
                        type="button"
                        className="btn-close"
                        onClick={handleClear}
                        style={{ background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer', color: '#666' }}
                    >
                        ×
                    </button>
                </div>
            ) : (
                <div className="search-input-wrapper">
                    <input
                        type="text"
                        className="form-control"
                        placeholder={placeholder}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onFocus={() => setIsOpen(true)}
                        onBlur={() => setTimeout(() => setIsOpen(false), 200)} // Delay to allow click
                    />
                    {isLoading && (
                        <div style={{ position: 'absolute', right: '10px', top: '38px' }}>
                            <LoadingSpinner size="small" />
                        </div>
                    )}
                </div>
            )}

            {isOpen && results.length > 0 && !selectedTeam && (
                <ul className="search-results-dropdown" style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    zIndex: 1000,
                    backgroundColor: 'white',
                    border: '1px solid #ddd',
                    borderRadius: '0 0 4px 4px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                    maxHeight: '300px',
                    overflowY: 'auto',
                    listStyle: 'none',
                    padding: 0,
                    marginTop: '2px'
                }}>
                    {results.map(team => (
                        <li
                            key={team.node_id}
                            onClick={() => handleSelect(team)}
                            style={{
                                padding: '0.75rem',
                                borderBottom: '1px solid #eee',
                                cursor: 'pointer',
                                transition: 'background 0.2s'
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f0f4ff'}
                            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'white'}
                        >
                            <div style={{ fontWeight: 500 }}>{team.legal_name}</div>
                            {team.founding_year && (
                                <div style={{ fontSize: '0.8rem', color: '#888' }}>
                                    Est. {team.founding_year} {team.dissolution_year ? `- ${team.dissolution_year}` : ''}
                                </div>
                            )}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
