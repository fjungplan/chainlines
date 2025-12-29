/**
 * Audit Log Page
 * 
 * Displays edit history with filtering by status, entity type, and user.
 * Allows moderators and admins to view, revert, and re-apply edits.
 * 
 * Uses maintenance-style layout consistent with other admin pages.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
    const navigate = useNavigate();

    // Filters
    const [statusFilters, setStatusFilters] = useState(['PENDING']); // Default to pending
    const [entityTypeFilter, setEntityTypeFilter] = useState('ALL');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: 'created_at', direction: 'desc' });

    // Pagination state
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(25);
    const [totalItems, setTotalItems] = useState(0);

    // State
    const [edits, setEdits] = useState([]);
    const [pendingCount, setPendingCount] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

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

            // Sorting
            params.sort_by = sortConfig.key;
            params.sort_order = sortConfig.direction;

            // Pagination
            params.skip = (currentPage - 1) * pageSize;
            params.limit = pageSize;

            const [editsResponse, countResponse] = await Promise.all([
                auditLogApi.getList(params),
                auditLogApi.getPendingCount()
            ]);

            // Handle new response format { items, total }
            if (editsResponse.data.items) {
                setEdits(editsResponse.data.items);
                setTotalItems(editsResponse.data.total);
            } else {
                // Fallback for older API if needed (though backend is updated)
                setEdits(editsResponse.data);
                // If it was array, total is length? No, assume array
                setTotalItems(editsResponse.data.length || 0);
            }

            setPendingCount(countResponse.data.count);
        } catch (err) {
            console.error('Failed to fetch audit log:', err);
            setError('Failed to load audit log. Please try again.');
        } finally {
            setLoading(false);
        }
    }, [canAccess, statusFilters, entityTypeFilter, startDate, endDate, sortConfig, currentPage, pageSize]);

    // Initial load
    useEffect(() => {
        fetchEdits();
    }, [fetchEdits]);

    // Handle filters change - reset page
    const handleStatusFilter = (status) => {
        setStatusFilters(prev => {
            if (prev.includes(status)) {
                return prev.filter(s => s !== status);
            } else {
                return [...prev, status];
            }
        });
        setCurrentPage(1);
    };

    const handleTypeFilter = (val) => {
        setEntityTypeFilter(val);
        setCurrentPage(1);
    };

    const handleDateChange = (start, end) => {
        if (start !== undefined) setStartDate(start);
        if (end !== undefined) setEndDate(end);
        setCurrentPage(1);
    };

    // Sorting
    const handleSort = (key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
        }));
        // Optional: Reset page on sort? Usually yes.
        setCurrentPage(1);
    };

    // View edit detail
    const handleViewEdit = (edit) => {
        navigate(`/audit-log/${edit.edit_id}`);
    };

    // Get sort indicator
    const getSortIndicator = (key) => {
        if (sortConfig.key !== key) return '';
        return sortConfig.direction === 'asc' ? ' ↑' : ' ↓';
    };

    // Pagination handlers
    const totalPages = Math.ceil(totalItems / pageSize);
    const startEntry = (currentPage - 1) * pageSize + 1;
    const endEntry = Math.min(currentPage * pageSize, totalItems);

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
                                onClick={() => handleStatusFilter(option.value)}
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
                            onChange={(e) => handleTypeFilter(e.target.value)}
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
                            onChange={(e) => handleDateChange(e.target.value, undefined)}
                            className="filter-input"
                        />
                        <span className="filter-separator">-</span>
                        <input
                            type="date"
                            value={endDate}
                            onChange={(e) => handleDateChange(undefined, e.target.value)}
                            className="filter-input"
                        />
                    </div>
                </div>

                {/* Content */}
                {loading && <LoadingSpinner />}
                {error && <ErrorDisplay message={error} />}

                {!loading && !error && (
                    <>
                        <div className="audit-log-table-container">
                            <table className="audit-log-table">
                                <thead>
                                    <tr>
                                        <th onClick={() => handleSort('status')} className="sortable">
                                            Status{getSortIndicator('status')}
                                        </th>
                                        <th onClick={() => handleSort('entity_type')} className="sortable">
                                            Entity{getSortIndicator('entity_type')}
                                        </th>
                                        <th onClick={() => handleSort('action')} className="sortable">
                                            Action{getSortIndicator('action')}
                                        </th>
                                        <th>Submitter</th>
                                        <th onClick={() => handleSort('created_at')} className="sortable">
                                            Submitted{getSortIndicator('created_at')}
                                        </th>
                                        <th>Reviewed By</th>
                                        <th>Summary</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {edits.length === 0 ? (
                                        <tr>
                                            <td colSpan="8" className="empty-message">
                                                No edits found matching the current filters.
                                            </td>
                                        </tr>
                                    ) : (
                                        edits.map(edit => (
                                            <tr
                                                key={edit.edit_id}
                                                onClick={() => handleViewEdit(edit)}
                                                className="clickable-row"
                                            >
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
                                                <td>{edit.reviewed_by ? (edit.reviewed_by.display_name || edit.reviewed_by.email) : '-'}</td>
                                                <td className="summary-cell">{edit.summary}</td>
                                                <td>
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleViewEdit(edit);
                                                        }}
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

                        <div className="pagination-bar">
                            <div className="pagination-info">
                                Showing {totalItems > 0 ? startEntry : 0} to {endEntry} of {totalItems} entries
                            </div>
                            <div className="pagination-controls">
                                <select
                                    value={pageSize}
                                    aria-label="Items per page"
                                    onChange={(e) => {
                                        setPageSize(Number(e.target.value));
                                        setCurrentPage(1);
                                    }}
                                    className="pagination-select"
                                >
                                    <option value={25}>25 per page</option>
                                    <option value={50}>50 per page</option>
                                    <option value={100}>100 per page</option>
                                </select>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    disabled={currentPage === 1}
                                    onClick={() => setCurrentPage(p => p - 1)}
                                >
                                    Previous
                                </Button>
                                <span className="page-number">Page {currentPage}</span>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    disabled={currentPage >= totalPages}
                                    onClick={() => setCurrentPage(p => p + 1)}
                                >
                                    Next
                                </Button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
