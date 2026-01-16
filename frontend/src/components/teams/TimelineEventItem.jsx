import React from 'react';
import { Link } from 'react-router-dom';
import {
    Merge,
    Split,
    ArrowRightLeft,
    Ghost,
    Share2,
    ArrowRight
} from 'lucide-react';
import '../../pages/TeamDetailPage.css';

/**
 * Renders a lineage event (Merge, Split, etc) in the team history list.
 */
const TimelineEventItem = ({ event }) => {
    const {
        event_type,
        year,
        related_team_name,
        related_team_id,
        related_era_name,
        direction,
        notes
    } = event;

    let icon = <ArrowRight size={18} />;
    let label = 'Event';
    let extraClass = 'event-generic';

    // Logic based on User Request:
    // Merge: Merged from / Merged into
    // Split: Split from / Split to
    // Legal transfer: Legal transfer from / Legal transfer to
    // Spiritual succession: Spiritual successor of / Spiritually succeeded by

    if (event_type === 'MERGE') {
        icon = <Merge size={18} />;
        if (direction === 'INCOMING') {
            label = 'Merged from';
            extraClass = 'event-merge-in';
        } else {
            label = 'Merged into';
            extraClass = 'event-merge-out';
        }
    } else if (event_type === 'SPLIT') {
        icon = <Split size={18} />;
        extraClass = 'event-split';
        if (direction === 'INCOMING') {
            label = 'Split from';
        } else {
            label = 'Split to'; // User requested "to"
        }
    } else if (event_type === 'LEGAL_TRANSFER') {
        // Service maps `LineageEventType.LEGAL_TRANSFER` to 'LEGAL_TRANSFER' (raw string)
        icon = <ArrowRightLeft size={18} />;
        extraClass = 'event-acquisition';
        if (direction === 'INCOMING') {
            label = 'Legal transfer from';
        } else {
            label = 'Legal transfer to';
        }
    } else if (event_type === 'SPIRITUAL_SUCCESSION') {
        // Service maps SPIRITUAL_SUCCESSION to 'SPIRITUAL_SUCCESSION'
        icon = <Ghost size={18} />;
        extraClass = 'event-revival';
        if (direction === 'INCOMING') {
            label = 'Spiritual successor of';
        } else {
            label = 'Spiritually succeeded by';
        }
    }

    return (
        <div className={`timeline-event ${extraClass}`}>
            <div className="event-year">{year}</div>
            <div className="event-content-wrapper">
                <div className="event-main-info">
                    <span className="event-icon" title={event_type}>{icon}</span>
                    <span className="event-label">{label}</span>
                    {related_team_id ? (
                        <Link to={`/team/${related_team_id}`} className="event-related-team-link">
                            {related_team_name}
                        </Link>
                    ) : (
                        <span className="event-related-team">{related_team_name}</span>
                    )}
                </div>

                {related_era_name && (
                    <div className="event-sub-info">
                        Era: {related_era_name}
                    </div>
                )}

                {notes && (
                    <div className="event-notes">
                        Note: {notes}
                    </div>
                )}
            </div>
        </div>
    );
};

export default TimelineEventItem;
