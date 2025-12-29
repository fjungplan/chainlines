/**
 * Audit Log Page
 * 
 * Displays edit history with filtering by status, entity type, and user.
 * Allows moderators and admins to view, revert, and re-apply edits.
 * 
 * Uses maintenance-style layout consistent with other admin pages.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { auditLogApi } from '../api/auditLog';
import { LoadingSpinner } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import Button from '../components/common/Button';
import { formatDateTime } from '../utils/dateUtils';
import './AuditLogPage.css';

// Status filter options
const STATUS_OPTIONS = [
    { value: 'PENDING', label: 'Pending', color: 'status-pending' },
    { value: 'APPROVED', label: 'Approved', color: 'status-approved' },
    { value: 'REJECTED', label: 'Rejected', color: 'status-rejected' },
    { value: 'REVERTED', label: 'Reverted', color: 'status-reverted' },
];

// Entity type options
const ENTITY_TYPE_OPTIONS = [
    { value: 'ALL', label: 'All Types' },
    { value: 'team_node', label: 'Team' },
    { value: 'team_era', label: 'Team Era' },
    { value: 'sponsor_master', label: 'Sponsor' },
    { value: 'sponsor_link', label: 'Sponsor Link' },
    { value: 'lineage_event', label: 'Lineage Event' },
];

export default function AuditLogPage() {
    const { isAdmin, isModerator } = useAuth();

    // State
    const [edits, setEdits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [pendingCount, setPendingCount] = useState(0);

    // Filters
    const [statusFilters, setStatusFilters] = useState(['PENDING']); // Default to pending
    const [entityTypeFilter, setEntityTypeFilter] = useState('ALL');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: 'submitted_at', direction: 'desc' });

    // Selected edit for detail view
    const [selectedEdit, setSelectedEdit] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);

    // Check permissions
    const canAccess = isAdmin() || isModerator();

    // Fetch edits based on current filters
    const fetchEdits = useCallback(async () => {
        if (!canAccess) return;

        setLoading(true);
        setError(null);

        try {
            const params = {};
            if (statusFilters.length > 0) {
                params.status = statusFilters;
            }
            if (entityTypeFilter !== 'ALL') {
                params.entity_type = entityTypeFilter;
            }
            if (startDate) {
                params.start_date = new Date(startDate).toISOString();
            }
            if (endDate) {
                // Set to end of day
                const end = new Date(endDate);
                end.setHours(23, 59, 59, 999);
                params.end_date = end.toISOString();
            }

            const [editsResponse, countResponse] = await Promise.all([
                auditLogApi.getList(params),
                auditLogApi.getPendingCount()
            ]);

            setEdits(editsResponse.data);
            setPendingCount(countResponse.data.count);
        } catch (err) {
            console.error('Failed to fetch audit log:', err);
            setError('Failed to load audit log. Please try again.');
        } finally {
            setLoading(false);
        }
    }, [canAccess, statusFilters, entityTypeFilter, startDate, endDate]);

    // Initial load
    useEffect(() => {
        fetchEdits();
    }, [fetchEdits]);

    // Toggle status filter
    const toggleStatusFilter = (status) => {
        setStatusFilters(prev => {
            if (prev.includes(status)) {
                return prev.filter(s => s !== status);
            } else {
                return [...prev, status];
            }
        });
    };

    // Sorting
    const handleSort = (key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
        }));
    };

    const sortedEdits = [...edits].sort((a, b) => {
        const { key, direction } = sortConfig;
        let valA = a[key];
        let valB = b[key];

        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();
        if (valA === null || valA === undefined) valA = '';
        if (valB === null || valB === undefined) valB = '';

        if (valA < valB) return direction === 'asc' ? -1 : 1;
        if (valA > valB) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    // View edit detail
    const handleViewEdit = async (edit) => {
        setDetailLoading(true);
        try {
            const response = await auditLogApi.getDetail(edit.edit_id);
            setSelectedEdit(response.data);
        } catch (err) {
            console.error('Failed to load edit detail:', err);
            setError('Failed to load edit details.');
        } finally {
            setDetailLoading(false);
        }
    };

    // Get sort indicator
    const getSortIndicator = (key) => {
        if (sortConfig.key !== key) return '';
        return sortConfig.direction === 'asc' ? ' ↑' : ' ↓';
    };

    // Permission check
    if (!canAccess) {
        return (
            <div className="audit-log-page">
                <div className="maintenance-page-container">
                    <ErrorDisplay message="You do not have permission to access this page." />
                </div>
            </div>
        );
    }

    return (
        <div className="audit-log-page">
            <div className="maintenance-page-container">
                {/* Header */}
                <div className="maintenance-header">
                    <div className="header-left">
                        <Link to="/" className="back-link">← Back to Timeline</Link>
                        <h1>Audit Log</h1>
                    </div>
                    <div className="header-right">
                        <span className="pending-badge">
                            {pendingCount} pending
                        </span>
                    </div>
                </div>

                {/* Filter Bar */}
                <div className="filter-bar">
                    <div className="filter-group">
                        <span className="filter-label">Status:</span>
                        {STATUS_OPTIONS.map(option => (
                            <Button
                                key={option.value}
                                variant={statusFilters.includes(option.value) ? 'primary' : 'ghost'}
                                size="sm"
                                onClick={() => toggleStatusFilter(option.value)}
                                className={`filter-btn ${option.color}`}
                            >
                                {option.label}
                            </Button>
                        ))}
                    </div>

                    <div className="filter-divider"></div>

                    <div className="filter-group">
                        <span className="filter-label">Type:</span>
                        <select
                            value={entityTypeFilter}
                            onChange={(e) => setEntityTypeFilter(e.target.value)}
                            className="filter-select"
                        >
                            {ENTITY_TYPE_OPTIONS.map(option => (
                                <option key={option.value} value={option.value}>
                                    {option.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="filter-divider"></div>

                    <div className="filter-group">
                        <span className="filter-label">Date:</span>
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="filter-input"
                        />
                        <span className="filter-separator">-</span>
                        <input
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="filter-input"
                        />
                    </div>
                </div>

                {/* Content */}
                {loading && <LoadingSpinner />}
                {error && <ErrorDisplay message={error} />}

                {!loading && !error && (
                    <div className="audit-log-table-container">
                        <table className="audit-log-table">
                            <thead>
                                <tr>
                                    <th onClick={() => handleSort('status')} className="sortable">
                                        Status{getSortIndicator('status')}
                                    </th>
                                    <th onClick={() => handleSort('entity_name')} className="sortable">
                                        Entity{getSortIndicator('entity_name')}
                                    </th>
                                    <th onClick={() => handleSort('action')} className="sortable">
                                        Action{getSortIndicator('action')}
                                    </th>
                                    <th>Submitter</th>
                                    <th onClick={() => handleSort('submitted_at')} className="sortable">
                                        Submitted{getSortIndicator('submitted_at')}
                                    </th>
                                    <th>Summary</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {sortedEdits.length === 0 ? (
                                    <tr>
                                        <td colSpan="7" className="empty-message">
                                            No edits found matching the current filters.
                                        </td>
                                    </tr>
                                ) : (
                                    sortedEdits.map(edit => (
                                        <tr key={edit.edit_id}>
                                            <td>
                                                <span className={`status-badge status-${edit.status.toLowerCase()}`}>
                                                    {edit.status}
                                                </span>
                                            </td>
                                            <td className="entity-cell">
                                                <span className="entity-type">{edit.entity_type}</span>
                                                <span className="entity-name">{edit.entity_name}</span>
                                            </td>
                                            <td>{edit.action}</td>
                                            <td>{edit.submitted_by?.display_name || edit.submitted_by?.email}</td>
                                            <td>{formatDateTime(edit.submitted_at)}</td>
                                            <td className="summary-cell">{edit.summary}</td>
                                            <td>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleViewEdit(edit)}
                                                >
                                                    View
                                                </Button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
