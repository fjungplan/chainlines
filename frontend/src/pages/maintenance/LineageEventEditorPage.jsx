import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { lineageApi } from '../../api/lineage';
import TeamSearch from '../../components/common/TeamSearch';
import { LoadingSpinner } from '../../components/Loading';
import '../../components/maintenance/SponsorEditor.css';

const EVENT_TYPES = [
    { value: 'MERGE', label: 'Merge' },
    { value: 'SPLIT', label: 'Split' },
    { value: 'LEGAL_TRANSFER', label: 'Legal Transfer' },
    { value: 'SPIRITUAL_SUCCESSION', label: 'Spiritual Succession' }
];

// Renamed to LineageEventEditor (props-based)
export default function LineageEventEditor({ eventId, onClose, onSuccess }) {
    const { user, isTrusted, isModerator, isAdmin } = useAuth();

    const isEditMode = !!eventId;
    const canDirectSave = isTrusted() || isAdmin() || isModerator();
    const canProtect = isModerator() || isAdmin();
    const showReasonField = !isModerator() && !isAdmin(); // Only hide for Mod/Admin

    const [loading, setLoading] = useState(isEditMode);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [warnings, setWarnings] = useState([]); // Array of warning strings

    // Form State
    const [eventType, setEventType] = useState('LEGAL_TRANSFER');
    const [eventYear, setEventYear] = useState(new Date().getFullYear());
    const [eventDate, setEventDate] = useState('');
    const [predecessorNode, setPredecessorNode] = useState(null);
    const [successorNode, setSuccessorNode] = useState(null);
    const [notes, setNotes] = useState('');
    const [sourceUrl, setSourceUrl] = useState('');
    const [isProtected, setIsProtected] = useState(false);
    const [reason, setReason] = useState('');

    // Load existing event for edit mode
    useEffect(() => {
        if (!isEditMode) return;

        const loadEvent = async () => {
            setLoading(true);
            try {
                const event = await lineageApi.getEvent(eventId);
                setEventType(event.event_type);
                setEventYear(event.event_year);
                setEventDate(event.event_date || '');
                setPredecessorNode({
                    node_id: event.predecessor_node_id,
                    legal_name: event.predecessor_name || 'Predecessor'
                });
                setSuccessorNode({
                    node_id: event.successor_node_id,
                    legal_name: event.successor_name || 'Successor'
                });
                setNotes(event.notes || '');
                setSourceUrl(event.source_url || '');
                setIsProtected(event.is_protected || false);
            } catch (err) {
                console.error("Failed to load event:", err);
                setError("Failed to load lineage event. It may not exist.");
            } finally {
                setLoading(false);
            }
        };
        loadEvent();
    }, [eventId, isEditMode]);

    // Validation Effect for Warnings
    useEffect(() => {
        const newWarnings = [];
        const year = parseInt(eventYear, 10);

        if (predecessorNode && !isNaN(year)) {
            // Predecessor should ideally exist just before or during the event year
            // Check if it dissolved way before
            if (predecessorNode.dissolution_year && predecessorNode.dissolution_year < year - 1) {
                newWarnings.push(`Predecessor '${predecessorNode.legal_name}' dissolved in ${predecessorNode.dissolution_year}, well before event year ${year}.`);
            }
            // Check if it started after
            if (predecessorNode.founding_year && predecessorNode.founding_year > year) {
                newWarnings.push(`Predecessor '${predecessorNode.legal_name}' was founded in ${predecessorNode.founding_year}, after event year ${year}.`);
            }
        }

        if (successorNode && !isNaN(year)) {
            // Successor should start around the event year or exist during it
            // Check if it dissolved before event
            if (successorNode.dissolution_year && successorNode.dissolution_year < year) {
                newWarnings.push(`Successor '${successorNode.legal_name}' dissolved in ${successorNode.dissolution_year}, before event year ${year}.`);
            }
            // Check if it starts way after (e.g. > 1 year gap)
            if (successorNode.founding_year && successorNode.founding_year > year + 1) {
                newWarnings.push(`Successor '${successorNode.legal_name}' was founded in ${successorNode.founding_year}, later than event year ${year}.`);
            }
        }

        setWarnings(newWarnings);
    }, [eventYear, predecessorNode, successorNode]);

    const handleSave = async (shouldClose = false) => {
        setError(null);

        // Validation
        if (!predecessorNode) {
            setError("Please select a Predecessor team.");
            return;
        }
        if (!successorNode) {
            setError("Please select a Successor team.");
            return;
        }
        if (predecessorNode.node_id === successorNode.node_id) {
            setError("Predecessor and Successor cannot be the same team.");
            return;
        }

        // Reason validation only for those who cannot direct save
        if (!canDirectSave && reason.length < 10) {
            setError("Reason must be at least 10 characters.");
            return;
        }

        setSubmitting(true);
        try {
            const payload = {
                event_type: eventType,
                event_year: parseInt(eventYear, 10),
                event_date: eventDate || null,
                predecessor_node_id: predecessorNode.node_id,
                successor_node_id: successorNode.node_id,
                notes: notes || null,
                source_url: sourceUrl || null,
                is_protected: canProtect ? isProtected : null,
                reason: reason
            };

            if (isEditMode) {
                await lineageApi.updateEvent(eventId, payload);
            } else {
                await lineageApi.createEvent(payload);
            }

            if (shouldClose) {
                onClose();
            } else {
                setSubmitting(false);
                if (onSuccess) onSuccess();
            }
        } catch (err) {
            console.error("Save failed:", err);
            let msg = "Failed to save lineage event.";
            if (err.response?.data?.detail) {
                const d = err.response.data.detail;
                if (typeof d === 'string') {
                    msg = d;
                } else if (Array.isArray(d)) {
                    msg = d.map(x => x.msg).join('; ');
                } else {
                    msg = JSON.stringify(d);
                }
            }
            setError(msg);
            setSubmitting(false);
        }
    };

    if (!user) {
        return <div className="sponsor-inner-container">Please log in to access this page.</div>;
    }

    if (loading) {
        return <div className="sponsor-inner-container"><LoadingSpinner /></div>;
    }

    const saveBtnLabel = isEditMode
        ? (canDirectSave ? "Save" : "Request Update")
        : (canDirectSave ? "Save" : "Request Creation");

    return (
        <div className="sponsor-inner-container centered-editor-container">
            {/* HEADER */}
            <div className="editor-header">
                <div className="header-left">
                    <button className="back-btn" onClick={onClose} title="Back to List">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                        </svg>
                    </button>
                    <h2>{isEditMode ? 'Edit Lineage Event' : 'New Lineage Event'}</h2>
                </div>
            </div>

            {/* Warnings Display */}
            {warnings.length > 0 && (
                <div className="warning-banner" style={{
                    backgroundColor: '#fff3cd',
                    color: '#856404',
                    padding: '1rem',
                    marginBottom: '1rem',
                    borderRadius: '4px',
                    border: '1px solid #ffeeba'
                }}>
                    <strong>Compatibility Warnings:</strong>
                    <ul style={{ margin: '0.5rem 0 0 0', paddingLeft: '1.5rem' }}>
                        {warnings.map((w, i) => <li key={i}>{w}</li>)}
                    </ul>
                </div>
            )}

            {/* SPLIT VIEW */}
            <div className="editor-split-view">
                <div className="editor-column details-column" style={{ flex: 1, maxWidth: '100%', borderRight: 'none' }}>
                    <div className="column-header">
                        <h3>Event Details</h3>
                        {canProtect && (
                            <label className="protected-toggle">
                                <input
                                    type="checkbox"
                                    checked={isProtected}
                                    onChange={e => setIsProtected(e.target.checked)}
                                />
                                <span>Protected Record</span>
                            </label>
                        )}
                        {isProtected && !canProtect && <span className="badge badge-warning">Protected (Read Only)</span>}
                    </div>

                    {error && <div className="error-banner">{error}</div>}

                    <form onSubmit={(e) => { e.preventDefault(); }}>
                        {/* Row 1: Type, Year, Date */}
                        <div className="form-row">
                            <div className="form-group" style={{ flex: 2 }}>
                                <label>Event Type *</label>
                                <select
                                    value={eventType}
                                    onChange={(e) => setEventType(e.target.value)}
                                >
                                    {EVENT_TYPES.map(t => (
                                        <option key={t.value} value={t.value}>{t.label}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Year *</label>
                                <input
                                    type="number"
                                    value={eventYear}
                                    onChange={(e) => setEventYear(e.target.value)}
                                    min={1900}
                                    max={2100}
                                    required
                                />
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Date (Optional)</label>
                                <input
                                    type="date"
                                    value={eventDate}
                                    onChange={(e) => setEventDate(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Row 2: Predecessor / Successor */}
                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1 }}>
                                <TeamSearch
                                    label="Predecessor Team *"
                                    placeholder="Search predecessor..."
                                    onSelect={setPredecessorNode}
                                    initialSelection={predecessorNode}
                                    excludeIds={successorNode ? [successorNode.node_id] : []}
                                />
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <TeamSearch
                                    label="Successor Team *"
                                    placeholder="Search successor..."
                                    onSelect={setSuccessorNode}
                                    initialSelection={successorNode}
                                    excludeIds={predecessorNode ? [predecessorNode.node_id] : []}
                                />
                            </div>
                        </div>

                        {/* Source URL */}
                        <div className="form-group">
                            <label>Source URL</label>
                            <input
                                type="url"
                                value={sourceUrl}
                                onChange={(e) => setSourceUrl(e.target.value)}
                                placeholder="https://example.com/source"
                            />
                        </div>

                        {/* Internal Notes */}
                        <div className="form-group">
                            <label>Internal Notes</label>
                            <textarea
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                rows={3}
                                placeholder="Additional context about this event..."
                            />
                        </div>

                        {/* Change Reason (Conditional) */}
                        {showReasonField && (
                            <div className="form-group">
                                <label>
                                    Reason for Request *
                                    <span style={{ fontWeight: 'normal', fontSize: '0.85rem', marginLeft: '0.5rem', color: '#666' }}>
                                        (Required for audit logs)
                                    </span>
                                </label>
                                <textarea
                                    value={reason}
                                    onChange={(e) => setReason(e.target.value)}
                                    placeholder="Please provide a source or reason for this change..."
                                    required
                                    rows={2}
                                    style={{ borderColor: '#fcd34d' }}
                                />
                            </div>
                        )}
                    </form>
                </div>
            </div>

            {/* FOOTER */}
            <div className="editor-footer">
                <button
                    type="button"
                    className="footer-btn cancel"
                    onClick={onClose}
                    disabled={submitting}
                >
                    Cancel
                </button>
                <div className="footer-actions-right">
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
                        {submitting ? 'Saving...' : 'Save & Close'}
                    </button>
                </div>
            </div>
        </div>
    );
}
