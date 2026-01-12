/**
 * My Edits Page
 * 
 * Displays the current user's edit history.
 * Visual copy of AuditLogPage but filtered to current user's submissions.
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
import './AuditLogPage.css'; // Reuse same styles

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

export default function MyEditsPage() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Data State
  const [edits, setEdits] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchingMore, setFetchingMore] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);

  // Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilters, setStatusFilters] = useState(['PENDING', 'APPROVED', 'REJECTED', 'REVERTED']); // All by default
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

  // Debounce Search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch edits function
  const fetchEdits = useCallback(async (isLoadMore = false) => {
    if (!isAuthenticated) return;

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

      // Search filter (summary, notes, entity name)
      if (debouncedSearch) params.search = debouncedSearch;

      // Status filter
      params.status = statusFilters;

      if (entityTypeFilter !== 'ALL') {
        params.entity_type = entityTypeFilter;
      }

      // Date filters
      if (startDate) params.start_date = new Date(startDate).toISOString();
      if (endDate) {
        const end = new Date(endDate);
        end.setHours(23, 59, 59, 999);
        params.end_date = end.toISOString();
      }

      // Sorting
      params.sort_by = sortConfig.key;
      params.sort_order = sortConfig.direction;

      // Pagination
      const currentLimit = PAGE_SIZE;
      const currentPage = isLoadMore ? pageRef.current : 1;
      params.skip = (currentPage - 1) * currentLimit;
      params.limit = currentLimit;

      const response = await auditLogApi.getMyList(params);

      let newItems = [];
      if (response.data.items) {
        newItems = response.data.items;
      } else {
        newItems = response.data;
      }

      // Determine if there are more
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
        pageRef.current = 2;
      }

    } catch (err) {
      console.error('Failed to fetch my edits:', err);
      setError('Failed to load your edits. Please try again.');
    } finally {
      setLoading(false);
      setFetchingMore(false);
    }
  }, [isAuthenticated, debouncedSearch, statusFilters, entityTypeFilter, startDate, endDate, sortConfig, loading, fetchingMore]);

  // Initial Load & Filter Changes
  useEffect(() => {
    fetchEdits(false);
    // eslint-disable-next-line
  }, [debouncedSearch, statusFilters, entityTypeFilter, startDate, endDate, sortConfig]);

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
    navigate(`/me/edits/${edit.edit_id}`);
  };

  const getSortIndicator = (key) => {
    if (sortConfig.key !== key) return '';
    return sortConfig.direction === 'asc' ? ' ↑' : ' ↓';
  };

  // Auth check
  if (!isAuthenticated) {
    return (
      <div className="maintenance-page-container">
        <ErrorDisplay message="Please sign in to view your edits." />
      </div>
    );
  }

  return (
    <div className="maintenance-page-container">
      <div className="maintenance-content-card">
        {/* Header */}
        <div className="audit-header">
          <div className="header-left">
            <Link to="/" className="back-link" title="Back to Timeline">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
              </svg>
            </Link>
            <h1>My Edits</h1>
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
                  <th onClick={() => handleSort('created_at')} className="sortable">
                    Submitted{getSortIndicator('created_at')}
                  </th>
                  <th>Reviewed By</th>
                  <th>Summary</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading && edits.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>
                      <LoadingSpinner message="Loading your edits..." />
                    </td>
                  </tr>
                ) : edits.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="empty-message">
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
                          <span className="entity-name">{edit.entity_name}</span>
                        </div>
                      </td>
                      <td>{edit.action}</td>
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

                {/* Infinite Scroll Sentinel */}
                {!loading && edits.length > 0 && (
                  <tr ref={loaderRef}>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '1rem', color: 'var(--color-text-secondary)' }}>
                      {fetchingMore ? (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                          <div className="spinner-small"></div> Loading more...
                        </div>
                      ) : hasMore ? (
                        <span style={{ opacity: 0 }}>Sentinel</span>
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
