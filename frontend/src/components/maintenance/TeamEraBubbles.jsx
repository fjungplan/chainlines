import { useState, useEffect, useRef } from 'react';
import { teamsApi } from '../../api/teams';
import { LoadingSpinner } from '../Loading';

export default function TeamEraBubbles({ nodeId, onEraSelect, onCreateEra, lastUpdate }) {
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
    }, [nodeId, lastUpdate]);

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

    // Scroll Preservation - find the scrolling parent
    const containerRef = useRef(null);
    const scrollKey = `team-era-scroll-${nodeId}`;

    // Find the scrolling parent container
    const findScrollParent = (element) => {
        if (!element) return null;
        let parent = element.parentElement;
        while (parent) {
            const overflow = window.getComputedStyle(parent).overflowY;
            if (overflow === 'auto' || overflow === 'scroll') {
                return parent;
            }
            parent = parent.parentElement;
        }
        return null;
    };

    // Save scroll position on scroll
    const handleScroll = (e) => {
        const scrollParent = e.currentTarget;
        if (scrollParent) {
            sessionStorage.setItem(scrollKey, scrollParent.scrollTop);
        }
    };

    // Restore scroll position after render
    useEffect(() => {
        if (eras.length > 0 && containerRef.current) {
            const scrollParent = findScrollParent(containerRef.current);
            if (scrollParent) {
                // Attach scroll listener
                scrollParent.addEventListener('scroll', handleScroll);

                // Restore saved position with a slight delay to ensure layout is complete
                requestAnimationFrame(() => {
                    const savedScroll = sessionStorage.getItem(scrollKey);
                    if (savedScroll) {
                        scrollParent.scrollTop = parseInt(savedScroll, 10);
                    }
                });

                return () => scrollParent.removeEventListener('scroll', handleScroll);
            }
        }
    }, [eras, nodeId]);

    if (loading) return <LoadingSpinner message="Loading eras..." />;

    return (
        <div className="era-bubbles-container" ref={containerRef}>


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
