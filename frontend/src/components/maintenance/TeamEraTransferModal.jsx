import { useState, useEffect } from 'react';
import { teamsApi } from '../../api/teams';
import { editsApi } from '../../api/edits';
import { LoadingSpinner } from '../Loading';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../common/Button';
import './SponsorEditor.css'; // Reuse modal/editor styling

/**
 * Modal for transferring TeamEras from a source team to the current target team.
 * 
 * @param {Object} props
 * @param {string} props.targetNodeId - The node_id of the team receiving the eras.
 * @param {Function} props.onClose - Callback to close the modal.
 * @param {Function} props.onSuccess - Callback after successful transfer.
 */
export default function TeamEraTransferModal({ targetNodeId, onClose, onSuccess }) {
    const { isTrusted, isAdmin, isModerator, canEdit } = useAuth();
    const canDirectEdit = isTrusted() || isAdmin() || isModerator();

    // Steps: 'search' -> 'select' -> 'confirm'
    const [step, setStep] = useState('search');

    // Search State
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);
    const [selectedSourceNode, setSelectedSourceNode] = useState(null);

    // Era Selection State
    const [sourceEras, setSourceEras] = useState([]);
    const [selectedEraIds, setSelectedEraIds] = useState(new Set());
    const [erasLoading, setErasLoading] = useState(false);

    // Submission State
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [reason, setReason] = useState('');

    const showReasonField = !isModerator() && !isAdmin();

    // Debounced search for source teams
    useEffect(() => {
        if (searchQuery.length < 2) {
            setSearchResults([]);
            return;
        }
        const timer = setTimeout(async () => {
            setSearchLoading(true);
            try {
                const res = await teamsApi.getTeams({ search: searchQuery, limit: 15 });
                // Filter out the target node itself
                setSearchResults(res.items.filter(t => t.node_id !== targetNodeId));
            } catch (err) {
                console.error("Search failed:", err);
            } finally {
                setSearchLoading(false);
            }
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery, targetNodeId]);

    // Load eras when a source node is selected
    useEffect(() => {
        if (!selectedSourceNode) return;
        const loadEras = async () => {
            setErasLoading(true);
            try {
                const eras = await teamsApi.getTeamEras(selectedSourceNode.node_id);
                // Sort by season_year descending (most recent first)
                setSourceEras(eras.sort((a, b) => b.season_year - a.season_year));
            } catch (err) {
                console.error("Failed to load eras:", err);
                setError("Could not load eras for the selected team.");
            } finally {
                setErasLoading(false);
            }
        };
        loadEras();
        setStep('select');
    }, [selectedSourceNode]);

    const handleSelectSource = (node) => {
        setSelectedSourceNode(node);
        setSelectedEraIds(new Set());
        setError(null);
    };

    const toggleEraSelection = (eraId) => {
        setSelectedEraIds(prev => {
            const next = new Set(prev);
            if (next.has(eraId)) {
                next.delete(eraId);
            } else {
                next.add(eraId);
            }
            return next;
        });
    };

    const handleConfirmStep = () => {
        if (selectedEraIds.size === 0) {
            setError("Please select at least one era to transfer.");
            return;
        }
        setError(null);
        setStep('confirm');
    };

    const handleTransfer = async () => {
        if (showReasonField && reason.length < 10) {
            setError("Please provide a reason for this change (at least 10 characters).");
            return;
        }

        setSubmitting(true);
        setError(null);

        try {
            const selectedErasData = sourceEras.filter(e => selectedEraIds.has(e.era_id));

            // Submit one edit per era (UPDATE to change node_id)
            for (const era of selectedErasData) {
                const payload = {
                    node_id: targetNodeId, // The new owner
                    reason: reason
                };
                await editsApi.updateEra(era.era_id, payload);
            }

            // Optionally, we could also submit edits to update source/target founding/dissolution years.
            // For now, this is left as a manual step or future enhancement.

            if (onSuccess) onSuccess();
            onClose();
        } catch (err) {
            console.error("Transfer failed:", err);
            // Handle Pydantic validation errors (detail is an array of error objects)
            let errorMessage = "Transfer failed.";
            const detail = err.response?.data?.detail;
            if (typeof detail === 'string') {
                errorMessage = detail;
            } else if (Array.isArray(detail) && detail.length > 0) {
                // Extract first error message from Pydantic ValidationError
                errorMessage = detail.map(e => e.msg || JSON.stringify(e)).join(', ');
            } else if (err.message) {
                errorMessage = err.message;
            }
            setError(errorMessage);
            setSubmitting(false);
        }
    };

    return (
        <div className="editor-overlay" onClick={onClose}>
            <div className="editor-modal" style={{ maxWidth: '600px', maxHeight: '80vh' }} onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div className="editor-header" style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #444' }}>
                    <div className="header-left">
                        <h2 style={{ fontSize: '1.25rem', margin: 0 }}>Transfer Eras from Another Team</h2>
                    </div>
                    <button className="back-btn" onClick={onClose} title="Close">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12L19 6.41Z" fill="currentColor" />
                        </svg>
                    </button>
                </div>

                {/* Body */}
                <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>
                    {error && <div className="error-banner">{error}</div>}

                    {/* Step 1: Search */}
                    {step === 'search' && (
                        <div>
                            <p style={{ color: '#a0aec0', marginBottom: '1rem' }}>
                                Search for the team you want to transfer eras FROM.
                            </p>
                            <div className="form-group">
                                <label>Search Teams</label>
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Type at least 2 characters..."
                                    autoFocus
                                />
                            </div>
                            {searchLoading && <LoadingSpinner />}
                            {!searchLoading && searchResults.length > 0 && (
                                <div className="brands-list" style={{ marginTop: '1rem' }}>
                                    {searchResults.map(node => (
                                        <div
                                            key={node.node_id}
                                            className="brand-item"
                                            onClick={() => handleSelectSource(node)}
                                        >
                                            <div className="brand-info">
                                                <div className="brand-name">{node.display_name || node.legal_name}</div>
                                                <div className="brand-display">{node.founding_year} - {node.dissolution_year || 'Active'}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Step 2: Select Eras */}
                    {step === 'select' && (
                        <div>
                            <p style={{ color: '#a0aec0', marginBottom: '0.5rem' }}>
                                Select eras to transfer from <strong style={{ color: '#fff' }}>{selectedSourceNode?.display_name || selectedSourceNode?.legal_name}</strong>:
                            </p>
                            <button
                                onClick={() => { setStep('search'); setSelectedSourceNode(null); setSourceEras([]); }}
                                className="secondary-btn small"
                                style={{ marginBottom: '1rem' }}
                            >
                                ← Change Source Team
                            </button>

                            {erasLoading && <LoadingSpinner />}
                            {!erasLoading && sourceEras.length === 0 && (
                                <div className="empty-panel">No eras found for this team.</div>
                            )}
                            {!erasLoading && sourceEras.length > 0 && (
                                <div className="brands-list">
                                    {sourceEras.map(era => (
                                        <label
                                            key={era.era_id}
                                            className={`brand-item ${selectedEraIds.has(era.era_id) ? 'active' : ''}`}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={selectedEraIds.has(era.era_id)}
                                                onChange={() => toggleEraSelection(era.era_id)}
                                                style={{ marginRight: '0.75rem' }}
                                            />
                                            <div className="brand-info">
                                                <div className="brand-name">{era.registered_name}</div>
                                                <div className="brand-display">
                                                    {era.season_year} {era.uci_code ? `(${era.uci_code})` : ''} - Tier {era.tier_level || '?'}
                                                </div>
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Step 3: Confirm */}
                    {step === 'confirm' && (
                        <div>
                            <p style={{ color: '#a0aec0', marginBottom: '1rem' }}>
                                You are about to transfer <strong style={{ color: '#fff' }}>{selectedEraIds.size}</strong> era(s) from
                                <strong style={{ color: '#fff' }}> {selectedSourceNode?.display_name || selectedSourceNode?.legal_name}</strong> to the target team.
                            </p>
                            <ul style={{ color: '#e2e8f0', marginBottom: '1rem', paddingLeft: '1.5rem' }}>
                                {sourceEras.filter(e => selectedEraIds.has(e.era_id)).map(era => (
                                    <li key={era.era_id}>{era.registered_name} ({era.season_year})</li>
                                ))}
                            </ul>

                            {showReasonField && (
                                <div className="form-group reason-group">
                                    <label>Reason for Request *</label>
                                    <textarea
                                        value={reason}
                                        onChange={e => setReason(e.target.value)}
                                        placeholder="Please explain why you are making this change..."
                                        required
                                        rows={2}
                                        style={{ borderColor: '#fcd34d' }}
                                    />
                                </div>
                            )}

                            <button
                                onClick={() => setStep('select')}
                                className="secondary-btn small"
                            >
                                ← Back to Selection
                            </button>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="editor-footer" style={{ padding: '0.75rem 1.5rem' }}>
                    <div className="footer-actions-left">
                        <Button variant="secondary" onClick={onClose} disabled={submitting}>Cancel</Button>
                    </div>
                    <div className="footer-actions-right">
                        {step === 'select' && (
                            <Button variant="primary" onClick={handleConfirmStep} disabled={selectedEraIds.size === 0}>
                                Review Transfer ({selectedEraIds.size})
                            </Button>
                        )}
                        {step === 'confirm' && (
                            <Button variant="primary" onClick={handleTransfer} disabled={submitting}>
                                {submitting ? 'Submitting...' : (canDirectEdit ? 'Confirm Transfer' : 'Request Transfer')}
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
