import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { lineageApi } from '../../api/lineage';
import { useAuth } from '../../contexts/AuthContext';
import { LoadingSpinner } from '../../components/Loading';
import LineageEventEditor from './LineageEventEditorPage';
import './LineageMaintenancePage.css';
import './TeamMaintenancePage.css';
import Button from '../../components/common/Button';

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
    const { canEdit, isModerator, isAdmin } = useAuth();
    const [events, setEvents] = useState([]);
    const [total, setTotal] = useState(0);
    // View State
    const [viewMode, setViewMode] = useState('list'); // 'list' | 'editor'
    const [selectedEventId, setSelectedEventId] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState('event_year');
    const [sortOrder, setSortOrder] = useState('desc');

    const PAGE_SIZE = 1000;

    const fetchEvents = async (search = '') => {
        setIsLoading(true);
        try {
            const data = await lineageApi.listEvents({
                skip: 0,
                limit: PAGE_SIZE,
                search: search || undefined,
                sort_by: sortBy,
                order: sortOrder
            });
            setEvents(data.items);
            setTotal(data.total);
        } catch (error) {
            console.error("Failed to fetch lineage events", error);
        } finally {
            setIsLoading(false);
        }
    };

    // Debounced search + Sort Trigger
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchEvents(searchQuery);
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery, sortBy, sortOrder]);

    const handleSort = (field) => {
        if (sortBy === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortBy(field);
            setSortOrder('desc');
        }
    };

    const handleAddClick = () => {
        setSelectedEventId(null);
        setViewMode('editor');
    };

    const handleEditClick = (eventId) => {
        setSelectedEventId(eventId);
        setViewMode('editor');
    };

    const handleCloseEditor = () => {
        setViewMode('list');
        setSelectedEventId(null);
        fetchEvents(searchQuery); // Refetch to update list + persist search
    };

    const handleSuccess = () => {
        fetchEvents(searchQuery);
        handleCloseEditor();
    };

    return (
        <div className="maintenance-page-container">
            {viewMode === 'editor' ? (
                <LineageEventEditor
                    eventId={selectedEventId}
                    onClose={handleCloseEditor}
                    onSuccess={handleSuccess}
                />
            ) : (
                <div className="maintenance-content-card">
                    <div className="lineage-header">
                        <h1>Lineage Events</h1>
                    </div>

                    <div className="lineage-controls">
                        <input
                            type="text"
                            placeholder="Search by team name (predecessor or successor)..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="search-input"
                            style={{ flex: 1, marginRight: '1rem' }}
                        />
                        {canEdit() && (
                            <Button variant="primary" onClick={handleAddClick}>
                                + Create New Event
                            </Button>
                        )}
                    </div>

                    <div className="team-list">
                        {isLoading ? (
                            <div style={{ padding: '2rem' }}><LoadingSpinner /></div>
                        ) : (
                            <table className="team-table">
                                <thead>
                                    <tr>
                                        <th
                                            style={{ width: '100px' }}
                                            className="sortable-header"
                                            onClick={() => handleSort('event_year')}
                                        >
                                            Year
                                            <span className={`sort-icon ${sortBy === 'event_year' ? 'active' : ''}`}>
                                                {sortBy === 'event_year' ? (sortOrder === 'asc' ? '▲' : '▼') : '⇅'}
                                            </span>
                                        </th>
                                        <th
                                            style={{ width: '140px' }}
                                            className="sortable-header"
                                            onClick={() => handleSort('event_type')}
                                        >
                                            Type
                                            <span className={`sort-icon ${sortBy === 'event_type' ? 'active' : ''}`}>
                                                {sortBy === 'event_type' ? (sortOrder === 'asc' ? '▲' : '▼') : '⇅'}
                                            </span>
                                        </th>
                                        <th>Predecessor</th>
                                        <th>Successor</th>
                                        <th>Notes</th>
                                        <th className="actions-col">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {events.map((event) => {
                                        const isProtectedEvent = event.is_protected;
                                        const canEditEvent = canEdit() && (!isProtectedEvent || isModerator() || isAdmin());

                                        return (
                                            <tr key={event.event_id}>
                                                <td>{event.event_year}</td>
                                                <td>
                                                    <EventTypeChip type={event.event_type} />
                                                    {isProtectedEvent && <span title="Protected">🛡️</span>}
                                                </td>
                                                <td>
                                                    {event.predecessor_node ? (event.predecessor_node.display_name || event.predecessor_node.legal_name) : '-'}
                                                </td>
                                                <td>
                                                    {event.successor_node ? (event.successor_node.display_name || event.successor_node.legal_name) : '-'}
                                                </td>
                                                <td style={{ maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                    {event.notes || '-'}
                                                </td>
                                                <td className="actions-col">
                                                    {canEditEvent && (
                                                        <Button
                                                            variant="secondary"
                                                            size="sm"
                                                            onClick={() => handleEditClick(event.event_id)}
                                                        >
                                                            Edit
                                                        </Button>
                                                    )}
                                                </td>
                                            </tr>
                                        );
                                    })}
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
            )}
        </div>
    );
};

export default LineageMaintenance;

