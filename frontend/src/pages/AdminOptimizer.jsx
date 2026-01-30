import React, { useState, useEffect, useCallback } from 'react';
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
                // If we were optimizing and it finished, refresh families to see new scores/dates
                if (isOptimizing) {
                    fetchFamilies();
                }
            }, POLLING_INTERVAL);
        }
        return () => clearInterval(interval);
    }, [isAdmin, fetchStatus, fetchFamilies, isOptimizing]);

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
                    <div className="header-right">
                        <Link to="/admin/optimizer/settings" className="btn btn-secondary btn-sm">
                            Settings
                        </Link>
                    </div>
                </div>

                <div className="optimizer-dashboard" style={{ flex: 1, overflowY: 'auto' }}>
                    {isOptimizing && (
                        <div className="alert alert-info" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#e3f2fd', borderLeft: '4px solid #2196f3', color: '#0d47a1' }}>
                            <i className="bi bi-gear-fill spin" style={{ marginRight: '0.5rem' }}></i>
                            Optimization in progress... {status.active_tasks} tasks active.
                        </div>
                    )}

                    {message && (
                        <div className="alert alert-success" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#e8f5e9', borderLeft: '4px solid #4caf50', color: '#1b5e20' }}>
                            {message}
                        </div>
                    )}

                    {status.last_error && (
                        <div className="alert alert-error" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#ffebee', borderLeft: '4px solid #f44336', color: '#b71c1c' }}>
                            <strong>Last Error:</strong> {status.last_error}
                        </div>
                    )}

                    <div className="actions" style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <button
                            className="btn btn-primary"
                            onClick={handleOptimize}
                            disabled={selectedFamilies.size === 0 || isOptimizing}
                        >
                            Optimize Selected ({selectedFamilies.size})
                        </button>
                        <button className="btn btn-secondary" onClick={fetchFamilies} disabled={loading}>
                            Refresh List
                        </button>
                    </div>

                    <div className="table-responsive" style={{ overflowX: 'auto' }}>
                        <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ borderBottom: '2px solid #eee', textAlign: 'left' }}>
                                    <th style={{ padding: '0.5rem' }}>
                                        <input
                                            type="checkbox"
                                            checked={families.length > 0 && selectedFamilies.size === families.length}
                                            onChange={toggleAll}
                                        />
                                    </th>
                                    <th style={{ padding: '0.5rem' }}>Family Hash</th>
                                    <th style={{ padding: '0.5rem' }}>Nodes</th>
                                    <th style={{ padding: '0.5rem' }}>Links</th>
                                    <th style={{ padding: '1rem', textAlign: 'center' }}>Status</th>
                                    <th style={{ padding: '1rem', textAlign: 'center' }}>Score</th>
                                    <th style={{ padding: '1rem' }}>Last Optimized</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>Loading families...</td></tr>
                                ) : families.length === 0 ? (
                                    <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>No cached families found.</td></tr>
                                ) : (
                                    families.map(f => (
                                        <tr key={f.family_hash} style={{ borderBottom: '1px solid #333' }}>
                                            <td style={{ padding: '0.5rem' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedFamilies.has(f.family_hash)}
                                                    onChange={() => toggleSelection(f.family_hash)}
                                                />
                                            </td>
                                            <td style={{ padding: '0.5rem' }} title={f.family_hash}>
                                                <code>{f.family_hash.substring(0, 8)}...</code>
                                            </td>
                                            <td style={{ padding: '0.5rem' }}>{f.node_count}</td>
                                            <td style={{ padding: '0.5rem' }}>{f.link_count}</td>
                                            <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                                <span className={`badge badge-${f.status}`}>
                                                    {f.status}
                                                </span>
                                            </td>
                                            <td style={{ padding: '0.5rem', textAlign: 'center' }}>
                                                {f.score?.toFixed(2) || 'N/A'}
                                            </td>
                                            <td style={{ padding: '0.5rem' }}>
                                                {f.optimized_at ? new Date(f.optimized_at).toLocaleString() : 'Never'}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            <style jsx="true">{`
                .spin {
                    animation: spin 2s linear infinite;
                    display: inline-block;
                }
                @keyframes spin {
                    100% { transform: rotate(360deg); }
                }
                .badge {
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.8rem;
                }
                .badge-cached { background-color: rgba(34, 197, 94, 0.2); color: #86efac; border: 1px solid rgba(34, 197, 94, 0.4); }
                .badge-stale { background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); }
                .badge-optimizing { background-color: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }
                .badge-no_cache { background-color: rgba(107, 114, 128, 0.2); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.4); }
                
                .optimizer-dashboard::-webkit-scrollbar {
                    width: 8px;
                }
                .optimizer-dashboard::-webkit-scrollbar-track {
                    background: var(--color-bg-primary);
                }
                .optimizer-dashboard::-webkit-scrollbar-thumb {
                    background: #555;
                    border-radius: 4px;
                }
                
                .table tr:hover {
                    background-color: var(--color-bg-tertiary);
                }
            `}</style>
        </div>
    );
}
