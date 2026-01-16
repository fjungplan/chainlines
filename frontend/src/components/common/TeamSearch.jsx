import { useState, useEffect, useRef } from 'react';
import { teamsApi } from '../../api/teams';
import { LoadingSpinner } from '../Loading';
import './TeamSearch.css';

/**
 * TeamSearch component for finding and selecting teams (nodes).
 * Autocomplete-style: Input remains visible.
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
    placeholder = "Type to search...",
    excludeIds = [],
    initialSelection = null,
    className = "",
    style = {}
}) {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(false);
    const [selectedTeam, setSelectedTeam] = useState(initialSelection); // Internal track

    const wrapperRef = useRef(null);

    // Sync from props
    useEffect(() => {
        if (initialSelection) {
            setSelectedTeam(initialSelection);
            setQuery(initialSelection.legal_name);
        } else {
            setSelectedTeam(null);
            // Only clear query if we don't have a local query? 
            // Better to clear it if the parent explicitly set null (reset)
            if (initialSelection === null) setQuery('');
        }
    }, [initialSelection]);

    // Click Outside listener to close dropdown consistently
    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    // Search effect
    useEffect(() => {
        // If query matches selected team name, don't search (avoid re-opening on select)
        if (selectedTeam && query === selectedTeam.legal_name) {
            setResults([]);
            return;
        }

        const fetchTeams = async () => {
            if (!query || query.length < 2) {
                setResults([]);
                return;
            }

            setIsLoading(true);
            try {
                const response = await teamsApi.getTeams({
                    search: query,
                    limit: 10
                });
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
    }, [query, excludeIds, selectedTeam]);

    const handleInputChange = (e) => {
        const val = e.target.value;
        setQuery(val);
        setIsOpen(true); // Re-open if typing

        // If user modifies text, clear selection state
        if (selectedTeam && val !== selectedTeam.legal_name) {
            setSelectedTeam(null);
            onSelect(null);
        }
    };

    const handleSelect = (team) => {
        setSelectedTeam(team);
        setQuery(team.legal_name);
        setIsOpen(false);
        onSelect(team);
    };

    return (
        <div className={`team-search-container ${className}`} style={style} ref={wrapperRef}>
            <label>{label}</label>

            <div className="search-input-wrapper">
                <input
                    type="text"
                    className="team-search-input"
                    placeholder={placeholder}
                    value={query}
                    onChange={handleInputChange}
                    onFocus={() => {
                        if (query.length >= 2 && !selectedTeam) setIsOpen(true);
                    }}
                />

                {isLoading && (
                    <div className="search-loader">
                        <LoadingSpinner size="small" />
                    </div>
                )}
            </div>

            {isOpen && results.length > 0 && (
                <ul className="team-search-dropdown">
                    {results.map(team => (
                        <li
                            key={team.node_id}
                            onClick={() => handleSelect(team)}
                        >
                            <div style={{ fontWeight: 500 }}>{team.legal_name}</div>
                            {team.founding_year && (
                                <div className="team-meta">
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
