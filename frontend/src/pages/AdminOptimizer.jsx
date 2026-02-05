import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { optimizerApi } from '../api/optimizer';
import '../components/common/Button.css';

const POLLING_INTERVAL = 5000;

export default function AdminOptimizer() {
    const { isAdmin } = useAuth();
    const [families, setFamilies] = useState([]);
    const [selectedFamilies, setSelectedFamilies] = useState(new Set());
    const [status, setStatus] = useState({ active_tasks: 0, last_run: null, last_error: null });
    const [loading, setLoading] = useState(true);
    const [isOptimizing, setIsOptimizing] = useState(false);
    const [message, setMessage] = useState(null);

    const [sortConfig, setSortConfig] = useState({ key: 'node_count', direction: 'desc' });

    const fetchFamilies = useCallback(async () => {
        try {
            const data = await optimizerApi.getFamilies();
            setFamilies(data);
        } catch (error) {
            console.error('Failed to fetch families:', error);
        }
    }, []);

    const fetchStatus = useCallback(async () => {
        try {
            const data = await optimizerApi.getStatus();
            setStatus(data);
            setIsOptimizing(data.active_tasks > 0);
        } catch (error) {
            console.error('Failed to fetch status:', error);
        }
    }, []);

    useEffect(() => {
        if (isAdmin()) {
            const init = async () => {
                setLoading(true);
                await Promise.all([fetchFamilies(), fetchStatus()]);
                setLoading(false);
            };
            init();
        }
    }, [isAdmin, fetchFamilies, fetchStatus]);

    useEffect(() => {
        let interval;
        if (isAdmin()) {
            interval = setInterval(() => {
                fetchStatus();
            }, POLLING_INTERVAL);
        }
        return () => clearInterval(interval);
    }, [isAdmin, fetchStatus]);

    // Handle data refresh when optimization starts/stops
    useEffect(() => {
        if (isAdmin()) {
            fetchFamilies();
        }
    }, [isAdmin, isOptimizing, fetchFamilies]);

    const toggleSelection = (hash) => {
        const next = new Set(selectedFamilies);
        if (next.has(hash)) {
            next.delete(hash);
        } else {
            next.add(hash);
        }
        setSelectedFamilies(next);
    };

    const toggleAll = () => {
        if (selectedFamilies.size === families.length) {
            setSelectedFamilies(new Set());
        } else {
            setSelectedFamilies(new Set(families.map(f => f.family_hash)));
        }
    };

    const handleDiscover = async () => {
        setLoading(true);
        try {
            const res = await optimizerApi.discoverFamilies();
            setMessage(res.message);
            // Refresh list after a short delay to allow background task to start/finish some work
            setTimeout(fetchFamilies, 2000);
            setTimeout(() => setMessage(null), 5000);
        } catch (error) {
            console.error('Failed to trigger discovery:', error);
            setMessage('Error: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleOptimize = async () => {
        const hashes = Array.from(selectedFamilies);
        if (hashes.length === 0) return;

        try {
            const res = await optimizerApi.triggerOptimization(hashes);
            setMessage(res.message);
            setIsOptimizing(true);
            setSelectedFamilies(new Set());
            // Clear message after 5 seconds
            setTimeout(() => setMessage(null), 5000);
        } catch (error) {
            console.error('Failed to trigger optimization:', error);
            setMessage('Error: ' + (error.response?.data?.detail || error.message));
        }
    };

    // Modal State for Logs
    const [showLogModal, setShowLogModal] = useState(false);
    const [selectedFamilyHash, setSelectedFamilyHash] = useState(null);
    const [logContent, setLogContent] = useState("");
    const [loadingLog, setLoadingLog] = useState(false);
    const logContainerRef = useRef(null);

    // Fetch Logs
    const handleViewLogs = async (hash) => {
        setSelectedFamilyHash(hash);
        setLogContent("");
        setShowLogModal(true);
        setLoadingLog(true);
        try {
            const lines = await optimizerApi.getFamilyLogs(hash);
            setLogContent(lines.join(''));
        } catch (error) {
            console.error('Failed to fetch logs:', error);
            setLogContent("Failed to load log file. It may not have been created yet.");
        } finally {
            setLoadingLog(false);
        }
    };

    // Auto-scroll logs
    useEffect(() => {
        if (showLogModal && logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [logContent, showLogModal]);

    const sortedFamilies = React.useMemo(() => {
        let sortableFamilies = [...families];
        if (sortConfig.key !== null) {
            sortableFamilies.sort((a, b) => {
                let aVal = a[sortConfig.key];
                let bVal = b[sortConfig.key];

                // Handle null/missing values
                if (aVal === null || aVal === undefined) aVal = (typeof bVal === 'number' ? -1 : '');
                if (bVal === null || bVal === undefined) bVal = (typeof aVal === 'number' ? -1 : '');

                if (typeof aVal === 'string') {
                    aVal = aVal.toLowerCase();
                    bVal = bVal.toLowerCase();
                }

                if (aVal < bVal) {
                    return sortConfig.direction === 'asc' ? -1 : 1;
                }
                if (aVal > bVal) {
                    return sortConfig.direction === 'asc' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableFamilies;
    }, [families, sortConfig]);

    const requestSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const getSortIndicator = (key) => {
        if (sortConfig.key !== key) return <i className="bi bi-arrow-down-up sort-icon-muted" style={{ fontSize: '0.8rem', opacity: 0.3, marginLeft: '4px' }}></i>;
        return sortConfig.direction === 'asc' ? <i className="bi bi-sort-up" style={{ marginLeft: '4px' }}></i> : <i className="bi bi-sort-down" style={{ marginLeft: '4px' }}></i>;
    };

    if (!isAdmin()) {
        return (
            <div className="maintenance-page-container">
                <div className="maintenance-content-card">
                    <div className="optimizer-header">
                        <h1>Access Denied</h1>
                    </div>
                    <div className="optimizer-dashboard">
                        <p>Admin access required.</p>
                        <Link to="/admin" className="btn btn-secondary" style={{ display: 'inline-block', marginTop: '1rem' }}>
                            Back to Admin Panel
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="maintenance-page-container">
            <div className="maintenance-content-card">
                {/* Header */}
                <div className="admin-header">
                    <div className="header-left">
                        <Link to="/admin" className="back-link" title="Back to Admin Panel">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                            </svg>
                        </Link>
                        <h1>Layout Optimizer</h1>
                    </div>
                </div>

                <div className="optimizer-dashboard" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '1.5rem' }}>
                    {isOptimizing && (
                        <div className="alert alert-info" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: 'rgba(59, 130, 246, 0.1)', borderLeft: '4px solid #3b82f6', color: '#93c5fd' }}>
                            <i className="bi bi-gear-fill spin" style={{ marginRight: '0.5rem' }}></i>
                            Optimization in progress... {status.active_tasks} tasks active.
                        </div>
                    )}

                    {message && (
                        <div className="alert alert-success" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: 'rgba(34, 197, 94, 0.1)', borderLeft: '4px solid #22c55e', color: '#86efac' }}>
                            {message}
                        </div>
                    )}

                    {status.last_error && (
                        <div className="alert alert-error" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid #ef4444', color: '#fca5a5' }}>
                            <strong>Last Error:</strong> {status.last_error}
                        </div>
                    )}

                    <div className="actions" style={{ marginBottom: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center', flexShrink: 0 }}>
                        <button
                            className="btn btn-primary"
                            onClick={handleOptimize}
                            disabled={selectedFamilies.size === 0 || isOptimizing}
                        >
                            Optimize Selected ({selectedFamilies.size})
                        </button>
                        <button className="btn btn-secondary" onClick={handleDiscover} disabled={loading}>
                            Discover New
                        </button>
                        <Link to="/admin/optimizer/settings" className="btn btn-secondary" style={{ marginLeft: 'auto' }}>
                            Settings
                        </Link>
                    </div>

                    <div className="scraper-scroll-content" style={{ flex: 1, overflowY: 'auto' }}>
                        <div className="run-history-section" style={{ padding: 0, border: 'none' }}>
                            <div className="history-table-container" style={{ minHeight: 'auto' }}>
                                <table className="history-table">
                                    <thead className="sortable-header">
                                        <tr>
                                            <th style={{ width: '40px' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={families.length > 0 && selectedFamilies.size === families.length}
                                                    onChange={toggleAll}
                                                />
                                            </th>
                                            <th onClick={() => requestSort('family_name')} style={{ cursor: 'pointer' }}>
                                                Name {getSortIndicator('family_name')}
                                            </th>
                                            <th onClick={() => requestSort('family_hash')} style={{ cursor: 'pointer' }}>
                                                Hash {getSortIndicator('family_hash')}
                                            </th>
                                            <th className="text-center" onClick={() => requestSort('node_count')} style={{ cursor: 'pointer' }}>
                                                Nodes {getSortIndicator('node_count')}
                                            </th>
                                            <th className="text-center" onClick={() => requestSort('link_count')} style={{ cursor: 'pointer' }}>
                                                Links {getSortIndicator('link_count')}
                                            </th>
                                            <th className="text-center" onClick={() => requestSort('score')} style={{ cursor: 'pointer' }}>
                                                Score {getSortIndicator('score')}
                                            </th>
                                            <th onClick={() => requestSort('optimized_at')} style={{ cursor: 'pointer' }}>
                                                Last Optimized {getSortIndicator('optimized_at')}
                                            </th>
                                            <th onClick={() => requestSort('status')} style={{ cursor: 'pointer' }}>
                                                Status {getSortIndicator('status')}
                                            </th>
                                            <th className="actions-col">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {loading ? (
                                            <tr><td colSpan="9" className="text-center p-8">Loading families...</td></tr>
                                        ) : sortedFamilies.length === 0 ? (
                                            <tr><td colSpan="9" className="text-center p-8">No cached families found.</td></tr>
                                        ) : (
                                            sortedFamilies.map(f => (
                                                <tr key={f.family_hash}>
                                                    <td>
                                                        <input
                                                            type="checkbox"
                                                            checked={selectedFamilies.has(f.family_hash)}
                                                            onChange={() => toggleSelection(f.family_hash)}
                                                        />
                                                    </td>
                                                    <td title={f.family_name} style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                        <strong>{f.family_name}</strong>
                                                    </td>
                                                    <td title={f.family_hash}>
                                                        <code>{f.family_hash.substring(0, 8)}</code>
                                                    </td>
                                                    <td className="text-center">{f.node_count}</td>
                                                    <td className="text-center">{f.link_count}</td>
                                                    <td className="text-center">
                                                        {f.score?.toFixed(2) || '0.00'}
                                                    </td>
                                                    <td>
                                                        {f.optimized_at ? (() => {
                                                            const d = new Date(f.optimized_at);
                                                            const dStr = d.toLocaleDateString('en-GB'); // DD/MM/YYYY
                                                            const tStr = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false }); // HH:mm
                                                            return `${dStr} ${tStr}`;
                                                        })() : '-'}
                                                    </td>
                                                    <td>
                                                        <span className={`status-badge status-${f.status || 'pending'}`}>
                                                            {f.status || 'UNKNOWN'}
                                                        </span>
                                                    </td>
                                                    <td className="actions-col">
                                                        <button
                                                            className="btn btn-secondary btn-sm"
                                                            onClick={() => handleViewLogs(f.family_hash)}
                                                            style={{ padding: '0.25rem 0.5rem', minWidth: 'auto' }}
                                                        >
                                                            Logs
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Log Modal */}
                {showLogModal && (
                    <div className="modal-overlay">
                        <div className="modal-content log-viewer-modal">
                            <div className="modal-header">
                                <h2>Optimizer Execution Log - Family {selectedFamilyHash?.substring(0, 8)}</h2>
                                <button
                                    onClick={() => {
                                        setShowLogModal(false);
                                        setSelectedFamilyHash(null);
                                    }}
                                    className="close-btn"
                                    title="Close"
                                >
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                </button>
                            </div>
                            <div className="log-modal-body">
                                <div className="log-container" ref={logContainerRef}>
                                    <pre>{loadingLog ? "Loading logs..." : (logContent || "No logs found for this run.")}</pre>
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button className="btn btn-secondary" onClick={() => {
                                    setShowLogModal(false);
                                    setSelectedFamilyHash(null);
                                }}>Close Viewer</button>
                            </div>
                        </div>
                    </div>
                )}

                <style jsx="true">{`
                .spin {
                    animation: spin 2s linear infinite;
                    display: inline-block;
                }
                @keyframes spin {
                    100% { transform: rotate(360deg); }
                }
                
                /* Import Scraper parity styles if not globally available */
                .status-badge {
                    display: inline-block;
                    padding: 0.25rem 0.5rem;
                    border-radius: var(--radius-sm);
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }
                .status-cached { background-color: rgba(34, 197, 94, 0.2); color: #86efac; border: 1px solid rgba(34, 197, 94, 0.4); }
                .status-stale { background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
                .status-optimizing { background-color: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }
                .status-pending { background-color: rgba(107, 114, 128, 0.2); color: #d1d5db; border: 1px solid rgba(107, 114, 128, 0.4); }

                /* Action Column Parity */
                .actions-col { text-align: right; width: 80px; }

                /* Force no underline for button-styled links */
                .btn {
                    text-decoration: none !important;
                }
                .btn:hover {
                    text-decoration: none !important;
                }
            `}</style>
            </div>
        </div>
    );
}
