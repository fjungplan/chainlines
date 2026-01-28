import React, { useState, useEffect, useCallback } from 'react';
import CenteredPageLayout from '../components/layout/CenteredPageLayout';
import Card from '../components/common/Card';
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
            <CenteredPageLayout>
                <Card title="Access Denied">
                    <p>Admin access required.</p>
                </Card>
            </CenteredPageLayout>
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
        <CenteredPageLayout>
            <Card title="Layout Optimizer">
                <div className="optimizer-dashboard">
                    {isOptimizing && (
                        <div className="alert alert-info" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#e3f2fd', borderLeft: '4px solid #2196f3' }}>
                            <i className="bi bi-gear-fill spin" style={{ marginRight: '0.5rem' }}></i>
                            Optimization in progress... {status.active_tasks} tasks active.
                        </div>
                    )}

                    {message && (
                        <div className="alert alert-success" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#e8f5e9', borderLeft: '4px solid #4caf50' }}>
                            {message}
                        </div>
                    )}

                    {status.last_error && (
                        <div className="alert alert-error" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#ffebee', borderLeft: '4px solid #f44336' }}>
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
                                    <th style={{ padding: '0.5rem' }}>Status</th>
                                    <th style={{ padding: '0.5rem' }}>Score</th>
                                    <th style={{ padding: '0.5rem' }}>Last Optimized</th>
                                </tr>
                            </thead>
                            <tbody>
                                {loading ? (
                                    <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>Loading families...</td></tr>
                                ) : families.length === 0 ? (
                                    <tr><td colSpan="7" style={{ textAlign: 'center', padding: '2rem' }}>No cached families found.</td></tr>
                                ) : (
                                    families.map(f => (
                                        <tr key={f.family_hash} style={{ borderBottom: '1px solid #eee' }}>
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
                                            <td style={{ padding: '0.5rem' }}>
                                                <span className={`badge badge-${f.status}`}>
                                                    {f.status}
                                                </span>
                                            </td>
                                            <td style={{ padding: '0.5rem' }}>
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
            </Card>
            <style>{`
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
                .badge-cached { background-color: #e8f5e9; color: #2e7d32; }
                .badge-stale { background-color: #fff3e0; color: #ef6c00; }
                .badge-optimizing { background-color: #e3f2fd; color: #1565c0; }
                .badge-no_cache { background-color: #f5f5f5; color: #757575; }
            `}</style>
        </CenteredPageLayout>
    );
}
