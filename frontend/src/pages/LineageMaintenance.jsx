import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { lineageApi } from '../api/lineage';
import { useAuth } from '../contexts/AuthContext';
import LineageEditor from '../components/maintenance/LineageEditor';
import { LoadingSpinner } from '../components/Loading';
import './LineageMaintenance.css';
import './TeamMaintenancePage.css';

const EventTypeChip = ({ type }) => {
    let className = 'event-chip';
    let label = type;

    switch (type) {
        case 'MERGE':
            className += ' merge';
            break;
        case 'SPLIT':
            className += ' split';
            break;
        case 'LEGAL_TRANSFER':
            className += ' transfer';
            label = 'TRANSFER';
            break;
        case 'SPIRITUAL_SUCCESSION':
            className += ' succession';
            label = 'SUCCESSION';
            break;
    }

    return <span className={className}>{label}</span>;
};

const LineageMaintenance = () => {
    const navigate = useNavigate();
    const { canEdit, isTrusted } = useAuth();
    const [events, setEvents] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [isLoading, setIsLoading] = useState(false);
    const [showEditor, setShowEditor] = useState(false);

    // Pagination
    const PAGE_SIZE = 1000; // Load all events (effectively)

    const fetchEvents = async () => {
        setIsLoading(true);
        try {
            const data = await lineageApi.listEvents({
                skip: 0,
                limit: PAGE_SIZE
            });
            setEvents(data.items);
            setTotal(data.total);
        } catch (error) {
            console.error("Failed to fetch lineage events", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchEvents();
    }, []);

    const handleAddClick = () => {
        setShowEditor(true);
    };

    return (
        <div className="maintenance-page-container">
            <div className="maintenance-content-card">
                <div className="lineage-header">
                    <h1>Lineage Events</h1>
                </div>

                <div className="lineage-controls">
                    {canEdit() && (
                        <button
                            className="btn btn-primary"
                            onClick={handleAddClick}
                        >
                            + New Event
                        </button>
                    )}
                </div>

                <div className="team-list">
                    {isLoading ? (
                        <div style={{ padding: '2rem' }}><LoadingSpinner /></div>
                    ) : (
                        <table className="team-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '80px' }}>Year</th>
                                    <th style={{ width: '120px' }}>Type</th>
                                    <th>Predecessor</th>
                                    <th>Successor</th>
                                    <th>Notes</th>
                                    <th className="actions-col">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {events.map((event) => (
                                    <tr key={event.event_id}>
                                        <td>{event.event_year}</td>
                                        <td>
                                            <EventTypeChip type={event.event_type} />
                                        </td>
                                        <td>
                                            {event.predecessor_node ? (event.predecessor_node.display_name || event.predecessor_node.legal_name) : '-'}
                                        </td>
                                        <td>
                                            {event.successor_node ? (event.successor_node.display_name || event.successor_node.legal_name) : '-'}
                                        </td>
                                        <td style={{ maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {event.notes}
                                        </td>
                                        <td className="actions-col">
                                            {canEdit() && (
                                                <button className="edit-button" disabled title="Editing existing events is not yet supported">
                                                    Edit
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                                {events.length === 0 && (
                                    <tr>
                                        <td colSpan={6} style={{ textAlign: 'center', padding: '2rem' }}>No events found</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>

            {/* Editor Dialog */}
            {showEditor && (
                <LineageEditor
                    open={showEditor}
                    onClose={() => setShowEditor(false)}
                    onSuccess={() => {
                        fetchEvents();
                        setShowEditor(false);
                    }}
                />
            )}
        </div>
    );
};

export default LineageMaintenance;
