/**
 * Audit Log Page
 * 
 * Displays edit history with filtering by status, entity type, and user.
 * Allows moderators and admins to view, revert, and re-apply edits.
 * 
 * Uses maintenance-style layout with Infinite Scroll.
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { auditLogApi } from '../api/auditLog';
import { LoadingSpinner } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import Button from '../components/common/Button';
import { formatDateTime } from '../utils/dateUtils';
import { useInfiniteScroll } from '../hooks/useInfiniteScroll';
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
    { value: 'sponsor_brand', label: 'Sponsor Brand' },
    { value: 'sponsor_link', label: 'Sponsor Link' },
    { value: 'lineage_event', label: 'Lineage Event' },
];

const PAGE_SIZE = 50;

export default function AuditLogPage() {
    const { isAdmin, isModerator } = useAuth();
    const navigate = useNavigate();



    // Data State
    const [edits, setEdits] = useState([]);
    const [loading, setLoading] = useState(false); // Initial load or filter change
    const [fetchingMore, setFetchingMore] = useState(false); // Infinite scroll load
    const [error, setError] = useState(null);
    const [hasMore, setHasMore] = useState(true);

    // Filter State
    const [searchQuery, setSearchQuery] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [statusFilters, setStatusFilters] = useState(['PENDING']);
    const [entityTypeFilter, setEntityTypeFilter] = useState('ALL');
    const [startDate, setStartDate] = useState(() => {
        const d = new Date();
        d.setFullYear(d.getFullYear() - 1);
        return d.toISOString().split('T')[0];
    });
    const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0]);
    const [sortConfig, setSortConfig] = useState({ key: 'created_at', direction: 'desc' });

    // Pagination tracking
    const pageRef = useRef(1);

    // Check permissions
    const canAccess = isAdmin() || isModerator();

    // Debounce Search
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(searchQuery);
        }, 500); // 500ms debounce

        return () => clearTimeout(timer);
    }, [searchQuery]);

    // Fetch edits function
    // isLoadMore: true = append, false = reset/replace
    const fetchEdits = useCallback(async (isLoadMore = false) => {
        if (!canAccess) return;

        // Prevent duplicate calls
        if (isLoadMore && fetchingMore) return;
        if (!isLoadMore && loading) return;

        if (isLoadMore) {
            setFetchingMore(true);
        } else {
            setLoading(true);
        }
        setError(null);

        try {
            const params = {};
            if (debouncedSearch) params.search = debouncedSearch;
            // Always send status to prevent backend from defaulting to PENDING
            params.status = statusFilters;
            if (entityTypeFilter !== 'ALL') params.entity_type = entityTypeFilter;
            if (startDate) params.start_date = new Date(startDate).toISOString();
            if (endDate) {
                const end = new Date(endDate);
                end.setHours(23, 59, 59, 999);
                params.end_date = end.toISOString();
            }

            // Sorting
            params.sort_by = sortConfig.key;
            params.sort_order = sortConfig.direction;

            // Pagination logic
            const currentLimit = PAGE_SIZE;
            // If loading more, skip = (page - 1) * limit
            // if resetting, page is 1, skip = 0
            const currentPage = isLoadMore ? pageRef.current : 1;
            params.skip = (currentPage - 1) * currentLimit;
            params.limit = currentLimit;

            const editsResponse = await auditLogApi.getList(params);

            let newItems = [];
            let total = 0;

            if (editsResponse.data.items) {
                newItems = editsResponse.data.items;
                total = editsResponse.data.total;
            } else {
                newItems = editsResponse.data;
                total = newItems.length; // Fallback
            }

            // Determine if there are more
            // If API returns total, we can use that. Or just check if items < limit
            if (newItems.length < currentLimit) {
                setHasMore(false);
            } else {
                setHasMore(true);
            }

            if (isLoadMore) {
                setEdits(prev => [...prev, ...newItems]);
                pageRef.current += 1;
            } else {
                setEdits(newItems);
                pageRef.current = 2; // Next page will be 2
                // Scroll to top of list if available?
                // document.querySelector('.audit-list-table-wrapper')?.scrollTo(0, 0); 
                // Handled layout effect?
            }

        } catch (err) {
            console.error('Failed to fetch audit log:', err);
            setError('Failed to load audit log. Please try again.');
        } finally {
            setLoading(false);
            setFetchingMore(false);
        }
    }, [canAccess, debouncedSearch, statusFilters, entityTypeFilter, startDate, endDate, sortConfig, loading, fetchingMore]);

    // Initial Load & Filter Changes
    // This effect runs when filters change. It triggers a "reset" load.
    useEffect(() => {
        // Reset state implicitly handled by fetchEdits(false) overwriting edits
        // But we want to ensure we don't trigger this on mount if we want strict control
        // React strict mode might double invoke.
        // We need to fetch on mount AND on filter change.
        fetchEdits(false);
        // eslint-disable-next-line
    }, [debouncedSearch, statusFilters, entityTypeFilter, startDate, endDate, sortConfig]);
    // Excluding fetchEdits from deps to avoid loop if fetchEdits changes (it shouldn't due to useCallback but safely handling)

    // Infinite Scroll Hook
    const { loaderRef } = useInfiniteScroll(() => {
        fetchEdits(true);
    }, { rootMargin: '100px' }, hasMore, fetchingMore || loading);


    // Handlers
    const handleSearch = (e) => {
        setSearchQuery(e.target.value);
    };

    const handleStatusFilter = (status) => {
        setStatusFilters(prev => {
            if (prev.includes(status)) return prev.filter(s => s !== status);
            return [...prev, status];
        });
        // Effect will trigger fetch
    };

    const handleTypeFilter = (val) => {
        setEntityTypeFilter(val);
    };

    const handleDateChange = (start, end) => {
        if (start !== undefined) setStartDate(start);
        if (end !== undefined) setEndDate(end);
    };

    const handleSort = (key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
        }));
    };

    const handleViewEdit = (edit) => {
        navigate(`/audit-log/${edit.edit_id}`);
    };

    const getSortIndicator = (key) => {
        if (sortConfig.key !== key) return '';
        return sortConfig.direction === 'asc' ? ' ↑' : ' ↓';
    };

    if (!canAccess) {
        return (
            <div className="maintenance-page-container">
                <ErrorDisplay message="You do not have permission to access this page." />
            </div>
        );
    }

    return (
        <div className="maintenance-page-container">
            <div className="maintenance-content-card">
                {/* Header */}
                <div className="admin-header">
                    <div className="header-left">
                        <Link to="/" className="back-link" title="Back to Timeline">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                            </svg>
                        </Link>
                        <h1>Audit Log</h1>
                    </div>
                </div>

                {/* Controls */}
                <div className="audit-controls">
                    <input
                        type="text"
                        placeholder="Search..."
                        value={searchQuery}
                        onChange={handleSearch}
                    />

                    <div className="filter-divider"></div>

                    <div className="filter-group filter-btn-group">
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

                    <div className="filter-date-group">
                        <input
                            type="date"
                            value={startDate}
                            onChange={(e) => handleDateChange(e.target.value, undefined)}
                            className="filter-input-date"
                        />
                        <span className="filter-separator">-</span>
                        <input
                            type="date"
                            value={endDate}
                            onChange={(e) => handleDateChange(undefined, e.target.value)}
                            className="filter-input-date"
                        />
                    </div>
                </div>

                {/* Content */}
                <div className="audit-list">
                    {/* Header Row (Sticky) */}
                    {/* To make header sticky within the scrollable area, we'll keep the table structure */}
                    <div className="audit-list-table-wrapper">
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
                                {loading && edits.length === 0 ? ( // Only show full spinner if initial load and no data
                                    <tr>
                                        <td colSpan="8" style={{ textAlign: 'center', padding: '2rem' }}>
                                            <LoadingSpinner message="Loading audit log..." />
                                        </td>
                                    </tr>
                                ) : edits.length === 0 ? ( // If not loading and no edits
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
                                            <td>
                                                <div className="entity-cell">
                                                    {/* Optional: Add Type indicator if needed, currently just name */}
                                                    {/* <span className="entity-type">{edit.entity_type}</span> */}
                                                    <span className="entity-name">{edit.entity_name}</span>
                                                </div>
                                            </td>
                                            <td>{edit.action}</td>
                                            <td>{edit.submitted_by?.display_name || edit.submitted_by?.email}</td>
                                            <td>{new Date(edit.submitted_at).toLocaleString()}</td>
                                            <td>{edit.reviewed_by ? (edit.reviewed_by.display_name || edit.reviewed_by.email) : '-'}</td>
                                            <td className="summary-cell">{edit.summary}</td>
                                            <td>
                                                <Button
                                                    variant="secondary"
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

                                {/* Ref Sentinel for Infinite Scroll - Only render if not initial loading and has data */}
                                {!loading && edits.length > 0 && (
                                    <tr ref={loaderRef}>
                                        <td colSpan="8" style={{ textAlign: 'center', padding: '1rem', color: 'var(--color-text-secondary)' }}>
                                            {fetchingMore ? (
                                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                                                    <div className="spinner-small"></div> Loading more...
                                                </div>
                                            ) : hasMore ? (
                                                <span style={{ opacity: 0 }}>Sentinel</span> // Invisible trigger
                                            ) : (
                                                <span className="end-of-list">End of list</span>
                                            )}
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
                {error && <ErrorDisplay error={error} onRetry={() => fetchEdits(false)} />}
            </div>
        </div>
    );
}
