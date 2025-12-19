import { useState, useEffect } from 'react';
import { teamsApi } from '../../api/teams';
import { LoadingSpinner } from '../Loading';
import { useAuth } from '../../contexts/AuthContext';
import './SponsorEditor.css'; // Reuse Sponsor Editor styles for consistency
import TeamEraBubbles from './TeamEraBubbles';

export default function TeamNodeEditor({ nodeId, onClose, onSuccess, onEraSelect }) {
    const { isAdmin } = useAuth();
    // For new teams, nodeId is null.

    // State
    const [loading, setLoading] = useState(!!nodeId);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const [formData, setFormData] = useState({
        legal_name: '',
        display_name: '',
        founding_year: new Date().getFullYear(),
        dissolution_year: '',
        is_protected: false,
        source_url: '',
        source_notes: ''
    });

    // Initial Load
    useEffect(() => {
        if (nodeId) {
            loadNodeData();
        }
    }, [nodeId]);

    const loadNodeData = async () => {
        setLoading(true);
        try {
            const data = await teamsApi.getTeam(nodeId);
            setFormData({
                legal_name: data.legal_name,
                display_name: data.display_name || '',
                founding_year: data.founding_year,
                dissolution_year: data.dissolution_year || '',
                is_protected: data.is_protected,
                source_url: data.source_url || '',
                source_notes: data.source_notes || ''
            });
        } catch (err) {
            console.error("Failed to load team:", err);
            setError("Failed to load team details");
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSave = async (shouldClose) => {
        setSubmitting(true);
        setError(null);
        try {
            // Convert empty strings to null for optional numbers/dates
            const payload = { ...formData };
            if (payload.dissolution_year === '') payload.dissolution_year = null;
            if (typeof payload.dissolution_year === 'string')
                payload.dissolution_year = payload.dissolution_year ? parseInt(payload.dissolution_year, 10) : null;
            if (typeof payload.founding_year === 'string')
                payload.founding_year = parseInt(payload.founding_year, 10);

            let currentNodeId = nodeId;

            if (nodeId) {
                await teamsApi.updateTeamNode(nodeId, payload);
            } else {
                const newTeam = await teamsApi.createTeamNode(payload);
                currentNodeId = newTeam.node_id;
                // Important: If we just created, we might need to tell parent the new ID
                if (onSuccess) onSuccess(currentNodeId);
            }

            if (shouldClose) {
                onClose(); // Back to List
            } else if (!nodeId) {
                // If created and staying, we should ideally switch to edit mode
                // But simplified: just notify success. Parent handles state update.
                if (onSuccess) onSuccess(currentNodeId);
            } else {
                setSubmitting(false);
            }
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "Failed to save team");
            setSubmitting(false);
        }
    };

    const handleDelete = async () => {
        if (!window.confirm("Are you sure you want to delete this team? This action cannot be undone.")) return;
        setSubmitting(true);
        try {
            await teamsApi.deleteTeamNode(nodeId);
            if (onClose) onClose();
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to delete team");
            setSubmitting(false);
        }
    };

    if (loading) return <div className="team-inner-container"><LoadingSpinner /></div>;

    return (
        <div className="team-inner-container centered-editor-container">
            {/* HEADER */}
            <div className="editor-header">
                <div className="header-left">
                    <button className="back-btn" onClick={onClose} title="Back to List">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                        </svg>
                    </button>
                    <h2>{nodeId ? 'Edit Team' : 'Create New Team'}</h2>
                </div>
            </div>

            {/* SPLIT CONTENT */}
            <div className="editor-split-view">
                {/* LEFT: FORM */}
                <div className="editor-column details-column">
                    <div className="column-header">
                        <h3>Team Details</h3>
                        {isAdmin() && (
                            <label className="protected-toggle">
                                <input
                                    type="checkbox"
                                    checked={formData.is_protected}
                                    onChange={e => handleChange('is_protected', e.target.checked)}
                                />
                                <span>Protected Record</span>
                            </label>
                        )}
                    </div>

                    {error && <div className="error-banner">{error}</div>}

                    <form onSubmit={(e) => { e.preventDefault(); }}>
                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1.5 }}>
                                <label>Legal Name *</label>
                                <input
                                    type="text"
                                    value={formData.legal_name}
                                    onChange={e => handleChange('legal_name', e.target.value)}
                                    required
                                />
                            </div>

                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Display Name</label>
                                <input
                                    type="text"
                                    value={formData.display_name}
                                    onChange={e => handleChange('display_name', e.target.value)}
                                    placeholder="Common name if different"
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Founding Year *</label>
                                <input
                                    type="number"
                                    min="1900"
                                    max="2100"
                                    value={formData.founding_year}
                                    onChange={e => handleChange('founding_year', e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Dissolution Year</label>
                                <input
                                    type="number"
                                    min="1900"
                                    max="2100"
                                    value={formData.dissolution_year}
                                    onChange={e => handleChange('dissolution_year', e.target.value)}
                                    placeholder="Active"
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Source URL</label>
                            <input
                                type="url"
                                value={formData.source_url}
                                onChange={e => handleChange('source_url', e.target.value)}
                            />
                        </div>

                        <div className="form-group">
                            <label>Internal Notes</label>
                            <textarea
                                value={formData.source_notes}
                                onChange={e => handleChange('source_notes', e.target.value)}
                                rows={3}
                            />
                        </div>
                    </form>
                </div>

                {/* RIGHT: BUBBLES */}
                <div className="editor-column brands-column">
                    <div className="column-header">
                        <h3>Eras (Seasons)</h3>
                        {nodeId && (
                            <button className="secondary-btn small" onClick={() => onEraSelect(null)}>
                                + Add Era
                            </button>
                        )}
                    </div>

                    {!nodeId ? (
                        <div className="empty-panel">
                            <p>Save team details first to manage eras.</p>
                        </div>
                    ) : (
                        <TeamEraBubbles
                            nodeId={nodeId}
                            onEraSelect={onEraSelect}
                            onCreateEra={() => onEraSelect(null)}
                        // We might need to adjust styles in TeamEraBubbles to look good here
                        // but for now, it should fit in the column.
                        />
                    )}
                </div>
            </div>

            {/* FOOTER */}
            <div className="editor-footer">
                <div className="footer-actions-left">
                    {nodeId && isAdmin() && (
                        <button
                            type="button"
                            className="footer-btn"
                            style={{ borderColor: '#991b1b', color: '#fca5a5' }}
                            onClick={handleDelete}
                            disabled={submitting}
                        >
                            Delete Team
                        </button>
                    )}
                    <button
                        type="button"
                        className="footer-btn"
                        onClick={onClose}
                        disabled={submitting}
                    >
                        Cancel
                    </button>
                </div>

                <div className="footer-actions-right">
                    <button
                        type="button"
                        className="footer-btn save"
                        onClick={() => handleSave(false)}
                        disabled={submitting}
                    >
                        Save
                    </button>
                    <button
                        type="button"
                        className="footer-btn save-close"
                        onClick={() => handleSave(true)}
                        disabled={submitting}
                    >
                        Save & Close
                    </button>
                </div>
            </div>
        </div>
    );
}
