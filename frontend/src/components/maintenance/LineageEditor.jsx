import React, { useState } from 'react';
import { editsApi } from '../../api/edits';
import '../../pages/LineageMaintenance.css'; // Uses modal styles

const EVENT_TYPES = {
    MERGE: 'MERGE',
    SPLIT: 'SPLIT'
};

const LineageEditor = ({ open, onClose, onSuccess }) => {
    const [eventType, setEventType] = useState(EVENT_TYPES.MERGE);
    const [year, setYear] = useState(new Date().getFullYear());
    const [reason, setReason] = useState('');
    const [error, setError] = useState(null);
    const [message, setMessage] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    // Merge State
    const [sourceIds, setSourceIds] = useState(['', '']); // Start with 2 slots
    const [newTeamName, setNewTeamName] = useState('');
    const [newTeamTier, setNewTeamTier] = useState(1);

    // Split State
    const [splitSourceId, setSplitSourceId] = useState('');
    const [splitNewTeams, setSplitNewTeams] = useState([
        { name: '', tier: 1 },
        { name: '', tier: 1 }
    ]);

    if (!open) return null;

    const isValid = () => {
        if (!reason || reason.length < 10) return false;
        if (eventType === EVENT_TYPES.MERGE) {
            if (sourceIds.some(id => !id)) return false;
            if (!newTeamName) return false;
        }
        if (eventType === EVENT_TYPES.SPLIT) {
            if (!splitSourceId) return false;
            if (splitNewTeams.some(t => !t.name)) return false;
        }
        return true;
    };

    const handleSourceIdChange = (index, value) => {
        const newIds = [...sourceIds];
        newIds[index] = value;
        setSourceIds(newIds);
    };

    const addSourceId = () => {
        if (sourceIds.length < 5) setSourceIds([...sourceIds, '']);
    };

    const removeSourceId = (index) => {
        if (sourceIds.length > 2) {
            setSourceIds(sourceIds.filter((_, i) => i !== index));
        }
    };

    const handleSplitTeamChange = (index, field, value) => {
        const newTeams = [...splitNewTeams];
        newTeams[index] = { ...newTeams[index], [field]: value };
        setSplitNewTeams(newTeams);
    };

    const addSplitTeam = () => {
        if (splitNewTeams.length < 5) {
            setSplitNewTeams([...splitNewTeams, { name: '', tier: 1 }]);
        }
    };

    const removeSplitTeam = (index) => {
        if (splitNewTeams.length > 2) {
            setSplitNewTeams(splitNewTeams.filter((_, i) => i !== index));
        }
    };

    const handleSubmit = async () => {
        setError(null);
        setSubmitting(true);
        try {
            let res;
            if (eventType === EVENT_TYPES.MERGE) {
                res = await editsApi.createMerge({
                    source_node_ids: sourceIds,
                    merge_year: parseInt(year),
                    new_team_name: newTeamName,
                    new_team_tier: parseInt(newTeamTier),
                    reason
                });
            } else {
                res = await editsApi.createSplit({
                    source_node_id: splitSourceId,
                    split_year: parseInt(year),
                    new_teams: splitNewTeams.map(t => ({ ...t, tier: parseInt(t.tier) })),
                    reason
                });
            }

            setMessage(res.message);
            setTimeout(() => {
                onClose();
                if (onSuccess) onSuccess();
            }, 1000);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "Failed to submit edit");
            setSubmitting(false);
        }
    };

    return (
        <div className="modal-overlay">
            <div className="modal-dialog">
                <div className="modal-header">
                    <h2>Create Lineage Event</h2>
                    <button className="icon-btn" onClick={onClose} aria-label="Close">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12L19 6.41Z" fill="currentColor" />
                        </svg>
                    </button>
                </div>

                <div className="modal-content">
                    {error && <div className="error-banner">{error}</div>}
                    {message && <div style={{ padding: '0.75rem', marginBottom: '1rem', background: 'rgba(16, 185, 129, 0.2)', color: '#6ee7b7', borderRadius: '6px' }}>{message}</div>}

                    <div className="form-group">
                        <label>Event Type</label>
                        <select
                            value={eventType}
                            onChange={(e) => setEventType(e.target.value)}
                        >
                            <option value={EVENT_TYPES.MERGE}>Merge (Combine Teams)</option>
                            <option value={EVENT_TYPES.SPLIT}>Split (Divide Team)</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Event Year</label>
                        <input
                            type="number"
                            value={year}
                            onChange={(e) => setYear(e.target.value)}
                        />
                    </div>

                    {eventType === EVENT_TYPES.MERGE && (
                        <div className="lineage-form-section">
                            <h3>Source Teams (to be merged)</h3>
                            {sourceIds.map((id, index) => (
                                <div className="input-row" key={index}>
                                    <input
                                        type="text"
                                        placeholder={`Source Team ID #${index + 1} (UUID)`}
                                        value={id}
                                        onChange={(e) => handleSourceIdChange(index, e.target.value)}
                                        style={{ flex: 1 }}
                                    />
                                    {sourceIds.length > 2 && (
                                        <button className="icon-btn danger" onClick={() => removeSourceId(index)}>
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 12H4" /></svg>
                                        </button>
                                    )}
                                </div>
                            ))}
                            {sourceIds.length < 5 && (
                                <button className="secondary-btn small" onClick={addSourceId}>
                                    + Add Source Team
                                </button>
                            )}

                            <h3 style={{ marginTop: '1.5rem', marginBottom: '1rem', color: '#a0aec0', fontSize: '0.95rem', textTransform: 'uppercase' }}>Resulting Team</h3>
                            <div className="form-group">
                                <label>New Team Name</label>
                                <input
                                    type="text"
                                    value={newTeamName}
                                    onChange={(e) => setNewTeamName(e.target.value)}
                                />
                            </div>
                            <div className="form-group">
                                <label>New Team Tier</label>
                                <select
                                    value={newTeamTier}
                                    onChange={(e) => setNewTeamTier(e.target.value)}
                                >
                                    <option value={1}>WorldTour</option>
                                    <option value={2}>ProTeam</option>
                                    <option value={3}>Continental</option>
                                </select>
                            </div>
                        </div>
                    )}

                    {eventType === EVENT_TYPES.SPLIT && (
                        <div className="lineage-form-section">
                            <h3>Source Team (to be split)</h3>
                            <div className="form-group">
                                <label>Source Team ID</label>
                                <input
                                    type="text"
                                    placeholder="Source Team UUID"
                                    value={splitSourceId}
                                    onChange={(e) => setSplitSourceId(e.target.value)}
                                />
                            </div>

                            <h3 style={{ marginTop: '1.5rem' }}>Resulting Teams</h3>
                            {splitNewTeams.map((team, index) => (
                                <div className="input-row" key={index}>
                                    <input
                                        type="text"
                                        placeholder={`Team #${index + 1} Name`}
                                        value={team.name}
                                        onChange={(e) => handleSplitTeamChange(index, 'name', e.target.value)}
                                        style={{ flex: 2 }}
                                    />
                                    <select
                                        value={team.tier}
                                        onChange={(e) => handleSplitTeamChange(index, 'tier', e.target.value)}
                                        style={{ flex: 1 }}
                                    >
                                        <option value={1}>WT</option>
                                        <option value={2}>Pro</option>
                                        <option value={3}>Conti</option>
                                    </select>
                                    {splitNewTeams.length > 2 && (
                                        <button className="icon-btn danger" onClick={() => removeSplitTeam(index)}>
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 12H4" /></svg>
                                        </button>
                                    )}
                                </div>
                            ))}
                            {splitNewTeams.length < 5 && (
                                <button className="secondary-btn small" onClick={addSplitTeam}>
                                    + Add Result Team
                                </button>
                            )}
                        </div>
                    )}

                    <div className="form-group">
                        <label>Reason for Change *</label>
                        <textarea
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            placeholder="Please explain why this event is needed and provide sources if possible."
                            rows={3}
                            style={{ borderColor: (!reason || reason.length < 10) ? '#fcd34d' : undefined }}
                        />
                        <div style={{ fontSize: '0.8rem', color: '#a0aec0', marginTop: '0.25rem' }}>
                            Required (min 10 chars)
                        </div>
                    </div>
                </div>

                <div className="modal-actions">
                    <button className="footer-btn" onClick={onClose} disabled={submitting}>Cancel</button>
                    <button
                        className="footer-btn save"
                        onClick={handleSubmit}
                        disabled={!isValid() || submitting}
                        style={{ border: '1px solid #4A90E2', color: '#fff' }}
                    >
                        {submitting ? 'Submitting...' : 'Submit Request'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default LineageEditor;
