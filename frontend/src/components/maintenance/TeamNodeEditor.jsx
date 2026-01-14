import { useState, useEffect } from 'react';
import { teamsApi } from '../../api/teams';
import { editsApi } from '../../api/edits';
import { LoadingSpinner } from '../Loading';
import { useAuth } from '../../contexts/AuthContext';
import './SponsorEditor.css'; // Reuse Sponsor Editor styles for consistency
import TeamEraBubbles from './TeamEraBubbles';
import TeamEraTransferModal from './TeamEraTransferModal';

export default function TeamNodeEditor({ nodeId, onClose, onSuccess, onEraSelect }) {
    const { isAdmin, isModerator, isTrusted, canEdit } = useAuth();
    // For new teams, nodeId is null.

    // State
    const [loading, setLoading] = useState(!!nodeId);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [showTransferModal, setShowTransferModal] = useState(false);

    const [formData, setFormData] = useState({
        legal_name: '',
        display_name: '',
        founding_year: new Date().getFullYear(),
        dissolution_year: '',
        is_protected: false,
        source_url: '',
        source_notes: '',
        reason: '' // For edit requests
    });

    // Determine Rights
    const canDirectEdit = isTrusted() || isAdmin() || isModerator();
    const isProtected = !!nodeId && formData.is_protected && !isModerator();
    const showReasonField = !isModerator() && !isAdmin();

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
                source_notes: data.source_notes || '',
                reason: ''
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
            // Validate Reason if field is shown
            if (showReasonField && (!formData.reason || formData.reason.length < 10)) {
                throw new Error("Please provide a reason for this change (at least 10 characters).");
            }

            // Convert empty strings to null for optional numbers/dates
            const payload = { ...formData };
            if (payload.dissolution_year === '') payload.dissolution_year = null;
            if (typeof payload.dissolution_year === 'string')
                payload.dissolution_year = payload.dissolution_year ? parseInt(payload.dissolution_year, 10) : null;
            if (typeof payload.founding_year === 'string')
                payload.founding_year = parseInt(payload.founding_year, 10);

            let message = "";

            if (nodeId) {
                // UPDATE - Always use Edits API to ensure audit log/reason is captured
                const requestData = {
                    node_id: nodeId,
                    legal_name: payload.legal_name,
                    display_name: payload.display_name,
                    founding_year: payload.founding_year,
                    dissolution_year: payload.dissolution_year,
                    source_url: payload.source_url,
                    source_notes: payload.source_notes,
                    is_protected: payload.is_protected,
                    reason: payload.reason
                };
                await editsApi.updateNode(requestData);
                message = canDirectEdit ? "Team updated successfully" : "Update request submitted for moderation";
            } else {
                // CREATE - Use Edits API to ensure audit log
                // Warning: We don't get the new ID back easily from Edits API in simplified mode.
                const requestData = {
                    legal_name: payload.legal_name,
                    registered_name: payload.display_name || payload.legal_name,
                    founding_year: payload.founding_year,
                    uci_code: null,
                    tier_level: 3,
                    reason: payload.reason
                };
                const response = await editsApi.createTeamEdit(requestData);
                // If direct edit, we get the entity ID back to switch mode
                const newNodeId = response.entity_id;
                message = canDirectEdit ? "Team created" : "Team creation request submitted for moderation";

                if (shouldClose) {
                    onClose();
                    if (onSuccess) onSuccess(newNodeId);
                } else {
                    // User wants to stay open
                    setSubmitting(false);
                    if (newNodeId && canDirectEdit) {
                        // Switch to Edit Mode (parent will update prop)
                        if (onSuccess) onSuccess(newNodeId);
                        // Optional: alert(message); 
                    } else if (!nodeId) {
                        // If pending, we can't edit it yet, so must close
                        onClose();
                        alert(message);
                    } else {
                        // Updating existing, just alert
                        alert(message);
                        if (onSuccess) onSuccess();
                    }
                }
            }
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || "Failed to save team");
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

    const saveBtnLabel = nodeId
        ? (canDirectEdit ? "Save" : "Request Update")
        : (canDirectEdit ? "Create Team" : "Request Creation");

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
                        {/* Only Moderators/Admins can see/toggle Protection */}
                        {isModerator() && (
                            <label className="protected-toggle">
                                <input
                                    type="checkbox"
                                    checked={formData.is_protected}
                                    onChange={e => handleChange('is_protected', e.target.checked)}
                                />
                                <span>Protected Record</span>
                            </label>
                        )}
                        {/* If protected and not moderator, show badge */}
                        {isProtected && <span className="badge badge-warning">Protected (Read Only)</span>}
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
                                    readOnly={isProtected}
                                />
                            </div>

                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Display Name</label>
                                <input
                                    type="text"
                                    value={formData.display_name}
                                    onChange={e => handleChange('display_name', e.target.value)}
                                    placeholder="Common name if different"
                                    readOnly={isProtected}
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
                                    readOnly={isProtected}
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
                                    readOnly={isProtected}
                                />
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Source URL</label>
                            <input
                                type="url"
                                value={formData.source_url}
                                onChange={e => handleChange('source_url', e.target.value)}
                                readOnly={isProtected}
                            />
                        </div>

                        <div className="form-group">
                            <label>Internal Notes</label>
                            <textarea
                                value={formData.source_notes}
                                onChange={e => handleChange('source_notes', e.target.value)}
                                rows={1}
                                style={{ minHeight: 'var(--input-height)', height: 'var(--input-height)', padding: '10px 1rem' }}
                                readOnly={isProtected}
                            />
                        </div>

                        {/* REASON FIELD FOR REQUESTS */}
                        {showReasonField && (
                            <div className="form-group reason-group">
                                <label>Reason for Request *</label>
                                <textarea
                                    value={formData.reason}
                                    onChange={e => handleChange('reason', e.target.value)}
                                    placeholder="Please explain why you are making this change..."
                                    required
                                    rows={2}
                                    style={{ borderColor: '#fcd34d' }}
                                />
                            </div>
                        )}
                    </form>
                </div>

                {/* RIGHT: BUBBLES */}
                <div className="editor-column brands-column">
                    <div className="column-header">
                        <h3>Eras (Seasons)</h3>
                        {/* Only show Add Era if node exists. If protected, maybe block adding eras unless Mod? */}
                        {/* Plan says "Only MODERATOR and ADMIN can edit records marked is_protected". 
                            Adding an Era technically edits the lineage, but Era itself is a child.
                            Usually Protection cascades. Let's block Add Era if isProtected on Node.
                        */}
                        {nodeId && !isProtected && (
                            <div style={{ display: 'flex', gap: '0.5rem' }}>
                                <button className="secondary-btn small" onClick={() => onEraSelect(null)}>
                                    + Add Era
                                </button>
                                <button className="secondary-btn small" onClick={() => setShowTransferModal(true)}>
                                    Transfer Eras
                                </button>
                            </div>
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
                            onCreateEra={!isProtected ? () => onEraSelect(null) : undefined}
                        />
                    )}
                </div>
            </div>

            {/* Transfer Modal */}
            {showTransferModal && (
                <TeamEraTransferModal
                    targetNodeId={nodeId}
                    onClose={() => setShowTransferModal(false)}
                    onSuccess={() => {
                        setShowTransferModal(false);
                        loadNodeData(); // Refresh data
                        if (onSuccess) onSuccess();
                    }}
                />
            )}

            {/* FOOTER */}
            <div className="editor-footer">
                <div className="footer-actions-left">
                    {nodeId && isAdmin() && (
                        <button
                            type="button"
                            className="footer-btn"
                            style={{ borderColor: '#991b1b', color: '#fca5a5' }}
                            onClick={handleDelete}
                            disabled={submitting || isProtected}
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
                    {!isProtected && (
                        <>
                            <button
                                type="button"
                                className="footer-btn save"
                                onClick={() => handleSave(false)}
                                disabled={submitting}
                            >
                                {saveBtnLabel}
                            </button>
                            <button
                                type="button"
                                className="footer-btn save-close"
                                onClick={() => handleSave(true)}
                                disabled={submitting}
                            >
                                {canDirectEdit ? "Save & Close" : "Request & Close"}
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
