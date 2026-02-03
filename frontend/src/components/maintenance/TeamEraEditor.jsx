import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { teamsApi } from '../../api/teams';
import { editsApi } from '../../api/edits';
import { sponsorsApi } from '../../api/sponsors';

import { LoadingSpinner } from '../Loading';
import SponsorManagerModal from './SponsorManagerModal';
import Button from '../common/Button';
import './SponsorEditor.css'; // Reuse Sponsor style
import TeamEraBubbles from './TeamEraBubbles';
import { IOC_CODES } from '../../utils/iocCodes';
import { getTierName } from '../../utils/tierUtils';

export default function TeamEraEditor({ eraId, nodeId, baseEraId, onSuccess, onDelete }) {
    // State
    const [loading, setLoading] = useState(!!eraId);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [stats, setStats] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(Date.now()); // Trigger for Bubbles refresh
    const lastSavedEraId = useRef(null); // Track ID of just-saved era to prevent stale reloading

    const [formData, setFormData] = useState({
        season_year: new Date().getFullYear(),
        valid_from: '',
        registered_name: '',
        tier_level: 1,
        uci_code: '',
        country_code: '',
        is_protected: false,
        reason: ''
    });

    const { user, isModerator, isAdmin, isTrusted, isEditor, canEdit } = useAuth();

    // UI Visibility: Only hide reason for Admins/Mods (Trusted must explain edits)
    const showReasonField = !isModerator() && !isAdmin();

    // Determine rights
    // If era exists (edit mode):
    // - Protected: Only MOD/ADMIN can direct save. Shared: View only? Or request?
    // - Unprotected: TRUSTED/MOD/ADMIN direct save. EDITOR requests.
    // If new (create mode):
    // - TRUSTED/MOD/ADMIN direct save. EDITOR requests.

    const isProtected = formData.is_protected;

    const canDirectSave = () => {
        if (isModerator() || isAdmin()) return true;
        if (isProtected) return false; // Only Mod/Admin can touch protected
        if (isTrusted()) return true;
        return false; // Regular editors must request
    };

    const isRequestMode = () => {
        return !canDirectSave() && isEditor(); // Request if can't save but is editor
    };

    const canModifyProtection = () => {
        return isModerator() || isAdmin();
    };

    const canDelete = () => {
        if (!eraId) return false;
        if (isProtected) return isModerator() || isAdmin(); // Only Mod/Admin can delete protected? Or just Admin? 
        // Let's say Mod/Admin can delete protected eras. 
        // Unprotected: Trusted/Mod/Admin.
        return isTrusted() || isModerator() || isAdmin();
    };

    const [isSponsorModalOpen, setIsSponsorModalOpen] = useState(false);
    const [isCountryOpen, setIsCountryOpen] = useState(false);

    const [prefilledSponsors, setPrefilledSponsors] = useState([]);

    useEffect(() => {
        if (eraId) {
            // Optimization: If we just saved this era, don't reload from API immediately.
            // The local state is already fresh and correct. Re-fetching might hit a stale cache
            // (eventual consistency) and "revert" the form to old/empty data.
            if (lastSavedEraId.current === eraId) {
                setLoading(false);
                return;
            }
            loadEraData();
            setPrefilledSponsors([]);
        } else if (nodeId) {
            loadLatestEraForPrepopulation();
        } else {
            setFormData(prev => ({ ...prev, registered_name: `Team ${prev.season_year}` }));
            setLoading(false);
        }
    }, [eraId, nodeId]);

    const loadLatestEraForPrepopulation = async () => {
        setLoading(true);
        try {
            const eras = await teamsApi.getTeamEras(nodeId);

            let sourceEra = null;

            if (baseEraId) {
                // Priority 1: Clone from specifically selected era
                sourceEra = eras.find(e => e.era_id === baseEraId);
            }

            if (!sourceEra && eras && eras.length > 0) {
                // Priority 2: Clone from latest era
                const sorted = eras.sort((a, b) => b.season_year - a.season_year);
                sourceEra = sorted[0];
            }

            if (sourceEra) {
                // If cloning from baseEraId (not latest), we might want to keep same year or same logic?
                // Logic: 
                // If cloning latest -> next year.
                // If cloning specific -> same info, maybe same year (conflict?) or next available?
                // User requirement: "pre-populated from the selected era". 
                // Usually this means COPY content. Year should probably still be incremented from LATEST to avoid conflict?
                // Or if I select 1990, maybe I want to create 1991? 
                // Let's stick to "Next Year after LATEST" for default Year, but Content from SELECTED.

                // Find latest year for default date
                const allYears = eras.map(e => e.season_year);
                const maxYear = Math.max(...allYears);
                const nextYear = maxYear + 1;

                setFormData({
                    season_year: nextYear,
                    valid_from: `${nextYear}-01-01`,
                    registered_name: sourceEra.registered_name,
                    tier_level: sourceEra.tier_level,
                    uci_code: sourceEra.uci_code || '',
                    country_code: sourceEra.country_code || '',
                    is_protected: false, // Don't copy protection status
                    reason: '' // Reset reason
                });

                // Fetch sponsors from SOURCE era to pre-populate
                try {
                    const links = await sponsorsApi.getEraLinks(sourceEra.era_id);
                    if (links.length > 0) {
                        setPrefilledSponsors(links);
                        // Populate stats for display
                        const total = links.reduce((s, l) => s + l.prominence_percent, 0);
                        const sortedLinks = [...links].sort((a, b) => a.rank_order - b.rank_order);
                        setStats({
                            count: links.length,
                            totalProminence: total,
                            allSponsors: sortedLinks
                        });
                    }
                } catch (e) {
                    console.warn("Failed to load prev sponsors", e);
                }
            } else {
                setFormData(prev => ({ ...prev, registered_name: `Team ${prev.season_year}` }));
            }
        } catch (e) {
            console.error("Pre-pop failed", e);
        } finally {
            setLoading(false);
        }
    };

    const loadEraData = async () => {
        setLoading(true);
        try {
            // Find era in list as we don't have getEra(id) yet
            if (!nodeId) throw new Error("Node ID required");
            const eras = await teamsApi.getTeamEras(nodeId);
            const era = eras.find(e => e.era_id === eraId);
            if (!era) {
                // If era not found in list (stale?), try fetching directly if API supports it?
                // Or throw specific error.
                // If we assume consistent read-after-write, it should be there.
                // If not, throwing here prevents "reverting to defaults" (which happens if we proceed with empty?)
                // Actually, if `era` is undefined, the code below would crash on `era.season_year` unless we catch it.
                throw new Error("Era not found (stale cache?)");
            }

            setFormData({
                season_year: era.season_year,
                valid_from: era.valid_from ? era.valid_from.split('T')[0] : '',
                registered_name: era.registered_name,
                tier_level: era.tier_level,
                uci_code: era.uci_code || '',
                country_code: era.country_code || '',
                is_protected: era.is_protected || false,
                reason: ''
            });

            loadSponsorStats();
        } catch (err) {
            console.error(err);
            setError("Failed to load era details");
        } finally {
            setLoading(false);
        }
    };

    const loadSponsorStats = async () => {
        try {
            const links = await sponsorsApi.getEraLinks(eraId);
            const total = links.reduce((s, l) => s + l.prominence_percent, 0);

            // Sort (copy first to be safe)
            const sorted = [...links].sort((a, b) => a.rank_order - b.rank_order);

            setStats({
                count: links.length,
                totalProminence: total,
                allSponsors: sorted
            });
        } catch (e) {
            console.warn("Stats load failed", e);
        }
    };

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSave = async (shouldClose) => {
        setSubmitting(true);
        setError(null);
        try {
            const payload = { ...formData };
            if (!payload.valid_from) payload.valid_from = `${payload.season_year}-01-01`;

            let resultId = eraId;

            if (eraId) {
                // UPDATE - FORCE Edit API usage to capture audit reason
                // Validation:
                if (showReasonField && (!payload.reason || payload.reason.length < 10)) {
                    throw new Error("Please provide a reason for this change (at least 10 characters).");
                }

                const reqPayload = {
                    era_id: eraId,
                    registered_name: payload.registered_name,
                    uci_code: payload.uci_code || null,
                    country_code: payload.country_code || null,
                    tier_level: payload.tier_level,
                    valid_from: payload.valid_from,
                    reason: payload.reason
                };

                await editsApi.editMetadata(reqPayload);
                const msg = canDirectSave() ? "Era updated successfully" : "Update request submitted for moderation";
                if (!canDirectSave()) alert(msg); // Only alert if request, direct save is silent/smooth usually? 
                // Or maybe alert for both for consistency? Sponsormaster alerts only if request (or if staying open).
                // Let's keep existing behavior:
                // Previous code did NOT alert on direct save success, just onSuccess().
                // I will alert if it's a request.
                if (!canDirectSave()) alert(msg);

                if (onSuccess) onSuccess(shouldClose ? undefined : eraId);

            } else {
                // CREATE
                if (canDirectSave()) {
                    // Direct Save via Teams API (To preserve Copy Sponsors feature which needs ID)
                    // Note: Reason is NOT captured here as TeamsAPI doesn't support it.
                    // Sanitize optional fields
                    const createPayload = {
                        ...payload,
                        uci_code: payload.uci_code || null,
                        country_code: payload.country_code || null
                    };

                    const res = await teamsApi.createTeamEra(nodeId, createPayload);
                    resultId = res.era_id;
                    // Handle prefilled sponsors copy for direct create
                    await copySponsors(resultId);
                    if (onSuccess) onSuccess(shouldClose ? undefined : resultId);
                } else {
                    // Request Mode via Edits API
                    if (!payload.reason || payload.reason.length < 10) {
                        throw new Error("A reason (min 10 chars) is required for edit requests.");
                    }
                    const reqPayload = {
                        node_id: nodeId,
                        season_year: payload.season_year,
                        registered_name: payload.registered_name,
                        uci_code: payload.uci_code || null,
                        country_code: payload.country_code || null,
                        tier_level: payload.tier_level,
                        reason: payload.reason
                    };
                    await editsApi.createEraEdit(reqPayload);
                    alert("Creation request submitted for moderation.");
                    if (onSuccess) onSuccess();
                }
            }

            // Track that we just saved this ID so useEffect doesn't clobber state with stale data
            if (resultId) {
                lastSavedEraId.current = resultId;
                setLastUpdate(Date.now());
            }

            if (!canDirectSave() || shouldClose) {
                // Done
            } else {
                // If staying open (Save & Continue), we must UPDATE form state with result
                // to prevent "reverting" if we just rely on refetching (which might be stale).
                // Actually, if we switch mode from CREATE to EDIT, parent will re-render us with eraId=resultId.
                // So we need to rely on the parent updating `eraId` prop.
                // BUT, `loadEraData` will trigger on prop change.
                // If `loadEraData` hits stale API, we revert.
                // FIX: Verify API data before overwriting if we just saved? 
                // OR: Maybe we should pre-seed the cache or just trust the parent update?
                // The parent calls `handleEraSuccess` which sets `selectedEraId`.
                // This updates `eraId` prop here. `useEffect` triggers `loadEraData`.
                // If `teamsApi.getTeamEras` is slow/stale, we lose data.

                // For now, let's rely on standard flow. If revert persists, we might need manual seed.
                // However, the user said "it reverts to 2009".
                // This suggests `loadEraData` is loading the old "latest" instead of the new one?
                // `loadEraData` finds by ID: `eras.find(e => e.era_id === eraId)`.
                // If the new era isn't in `eras` list returned by API yet, `find` returns undefined.
                // Then `if (!nodeId) throw...` -> Error.
                // Wait, if `find` returns undefined, it throws "Era not found".
                // The user says "reverts to 2009". This sounds like `loadLatestEraForPrepopulation` logic running again?
                // If `eraId` is set, we run `loadEraData`. 
                // If `loadEraData` fails effectively, maybe something resets?

                // CRITICAL: We should update `submitting` AFTER parent update?
                // Actually, let's just finish here. Parent transition should be fast.
                setSubmitting(false);
            }
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || "Failed to save era");
            setSubmitting(false);
        }
    };

    const copySponsors = async (targetEraId) => {
        if (prefilledSponsors.length > 0) {
            try {
                const uniqueBrands = new Set();
                const sponsorPayload = prefilledSponsors
                    .filter(l => {
                        const bid = l.brand?.brand_id || l.brand_id;
                        if (uniqueBrands.has(bid)) return false;
                        uniqueBrands.add(bid);
                        return true;
                    })
                    .map(l => {
                        // Auto-detect redundancy
                        let finalOverride = l.hex_color_override;
                        if (finalOverride && l.brand?.default_hex_color &&
                            finalOverride.toLowerCase() === l.brand.default_hex_color.toLowerCase()) {
                            finalOverride = null;
                        }

                        return {
                            brand_id: l.brand?.brand_id || l.brand_id,
                            rank_order: l.rank_order,
                            prominence_percent: l.prominence_percent,
                            hex_color_override: finalOverride
                        };
                    });
                await sponsorsApi.replaceEraLinks(targetEraId, sponsorPayload);
            } catch (spErr) {
                console.error("Failed to copy sponsors", spErr);
            }
        }
    };

    const handleDelete = async () => {
        if (!canDelete()) return;
        if (!window.confirm("Delete this era?")) return;
        setSubmitting(true);
        try {
            await teamsApi.deleteTeamEra(eraId);
            if (onDelete) onDelete();
        } catch (err) {
            setError("Failed to delete era");
            setSubmitting(false);
        }
    };

    // Callback for right-col clicks: navigate to sibling era (Switch ID). 
    // Parent handles "onSuccess" usually as "Back", but if we pass a specific ID, parent should switch view.
    // We reuse onSuccess signature: if (id) -> switch, if () -> back.
    // If id === 'NEW', switch to create mode.
    const handleEraSwitch = (newId) => {
        if (onSuccess) onSuccess(newId);
    };

    if (loading) return <div className="team-inner-container"><LoadingSpinner /></div>;

    return (
        <div className="team-inner-container centered-editor-container">
            <div className="editor-header">
                <div className="header-left">
                    <Button variant="ghost" className="back-btn" onClick={() => onSuccess && onSuccess()} title="Back to Team">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                        </svg>
                    </Button>

                    <h2>{eraId ? `Edit Era (Season): ${formData.season_year}` : 'Add New Era (Season)'}</h2>
                </div>
                <div className="header-right">
                    {/* Protection moved to Column Header */}
                </div>
            </div>

            <div className="editor-split-view">
                {/* FORM */}
                <div className="editor-column details-column">
                    <div className="column-header">
                        <h3>Era (Season) Properties</h3>
                        {canModifyProtection() && (
                            <label className="protected-toggle">
                                <input
                                    type="checkbox"
                                    checked={formData.is_protected}
                                    onChange={e => handleChange('is_protected', e.target.checked)}
                                />
                                <span>Protected Record</span>
                            </label>
                        )}
                        {isProtected && !canModifyProtection() && <span className="badge badge-warning">Protected (Read Only)</span>}
                    </div>

                    {error && <div className="error-banner">{error}</div>}

                    <form onSubmit={(e) => { e.preventDefault(); }}>
                        <div className="form-row">
                            <div className="form-group" style={{ flex: '0 0 100px' }}>
                                <label>Season *</label>
                                <input
                                    type="number"
                                    value={formData.season_year}
                                    onChange={e => handleChange('season_year', parseInt(e.target.value))}
                                    required
                                    readOnly={isProtected && !isModerator() && !isAdmin()}
                                />
                            </div>
                            <div className="form-group" style={{ flex: 2 }}>
                                <label>Registered Name *</label>
                                <input
                                    type="text"
                                    value={formData.registered_name}
                                    onChange={e => handleChange('registered_name', e.target.value)}
                                    required
                                    readOnly={isProtected && !isModerator() && !isAdmin()}
                                />
                            </div>
                            <div className="form-group" style={{ flex: '0 0 100px' }}>
                                <label>UCI Code</label>
                                <input
                                    type="text"
                                    value={formData.uci_code}
                                    onChange={e => handleChange('uci_code', e.target.value)}
                                    maxLength={3}
                                    readOnly={isProtected && !isModerator() && !isAdmin()}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group" style={{ flex: 2 }}>
                                <label>Tier Level *</label>
                                <select
                                    value={formData.tier_level}
                                    onChange={e => handleChange('tier_level', parseInt(e.target.value))}
                                    disabled={isProtected && !isModerator() && !isAdmin()}
                                >
                                    <option value={1}>Tier 1 - {getTierName(1, formData.season_year)}</option>
                                    <option value={2}>Tier 2 - {getTierName(2, formData.season_year)}</option>
                                    <option value={3}>Tier 3 - {getTierName(3, formData.season_year)}</option>
                                </select>
                            </div>
                            <div className="form-group" style={{ flex: 0.6, position: 'relative' }}>
                                <label>Country</label>
                                <input
                                    type="text"
                                    value={formData.country_code}
                                    onChange={e => {
                                        handleChange('country_code', e.target.value.toUpperCase());
                                        setIsCountryOpen(true);
                                    }}
                                    onFocus={() => setIsCountryOpen(true)}
                                    placeholder="ATH"
                                    maxLength={3}
                                    readOnly={isProtected && !isModerator() && !isAdmin()}
                                />
                                {isCountryOpen && (
                                    <>
                                        <div
                                            style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 99 }}
                                            onClick={() => setIsCountryOpen(false)}
                                        />
                                        <ul className="custom-dropdown-list" style={{ zIndex: 100, minWidth: '300px', whiteSpace: 'nowrap' }}>
                                            {IOC_CODES.filter(c =>
                                                c.code.includes(formData.country_code.toUpperCase()) ||
                                                c.name.toUpperCase().includes(formData.country_code.toUpperCase())
                                            ).map(c => (
                                                <li
                                                    key={c.code}
                                                    onClick={() => {
                                                        handleChange('country_code', c.code);
                                                        setIsCountryOpen(false);
                                                    }}
                                                >
                                                    <strong>{c.code}</strong> - {c.name}
                                                </li>
                                            ))}
                                            {IOC_CODES.filter(c => c.code.includes(formData.country_code.toUpperCase())).length === 0 && (
                                                <li style={{ color: '#666', fontStyle: 'italic', cursor: 'default' }}>
                                                    No matches
                                                </li>
                                            )}
                                        </ul>
                                    </>
                                )}
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Valid From</label>
                                <input
                                    type="date"
                                    value={formData.valid_from}
                                    onChange={e => handleChange('valid_from', e.target.value)}
                                    readOnly={isProtected && !isModerator() && !isAdmin()}
                                />
                            </div>
                        </div>

                        {/* REASON FIELD FOR REQUESTS OR TRUSTED EDITS */}
                        {showReasonField && (eraId || !canDirectSave()) && (
                            <div className="form-row">
                                <div className="form-group full-width">
                                    <label>Reason / Change Log *</label>
                                    <textarea
                                        value={formData.reason}
                                        onChange={e => handleChange('reason', e.target.value)}
                                        placeholder={eraId ? "Please explain this change (captured in audit log)..." : "Please provide a reason for this request..."}
                                        rows={2}
                                        required
                                        style={{ width: '100%', resize: 'vertical', borderColor: '#fcd34d' }}
                                    />
                                    <small style={{ color: '#666' }}>Min 10 characters.</small>
                                </div>
                            </div>
                        )}

                        {/* Sponsor Section */}
                        {(eraId || stats) && (
                            <div className="era-sponsors-section">
                                <div className="section-header">
                                    <label>Era Sponsors</label>
                                    {eraId ? (
                                        <Button
                                            variant="secondary"
                                            size="sm"
                                            onClick={() => setIsSponsorModalOpen(true)}
                                        >
                                            Manage Sponsors
                                        </Button>
                                    ) : (
                                        <span style={{ fontSize: '0.8rem', color: '#666', fontStyle: 'italic' }}>
                                            (Sponsors copied from previous era. Save to edit.)
                                        </span>
                                    )}
                                </div>

                                {stats ? (
                                    <div className="sponsors-summary">
                                        <div className="top-sponsors-list">
                                            {stats.allSponsors && stats.allSponsors.length > 0 ? (
                                                stats.allSponsors.map(link => (
                                                    <div key={link.link_id} className="mini-sponsor-pill">
                                                        <div className="color-dot" style={{ background: link.hex_color_override || link.brand?.default_hex_color }}></div>
                                                        <span className="name">{link.brand?.brand_name}</span>
                                                        <span className="percent">{link.prominence_percent}%</span>
                                                    </div>
                                                ))
                                            ) : (
                                                <span style={{ color: '#666', fontStyle: 'italic' }}>No sponsors linked.</span>
                                            )}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="loading-text">Loading sponsor data...</div>
                                )}
                            </div>
                        )}
                    </form>
                </div>

                {/* RIGHT: CONTEXT LIST */}
                <div className="editor-column brands-column">
                    <div className="column-header">
                        <h3>Team Timeline</h3>
                        <Button variant="secondary" size="sm" onClick={() => handleEraSwitch('NEW')}>
                            + New Era
                        </Button>
                    </div>
                    <TeamEraBubbles
                        nodeId={nodeId}
                        onEraSelect={handleEraSwitch}
                        onCreateEra={() => handleEraSwitch('NEW')}
                        lastUpdate={lastUpdate}
                    />
                </div>
            </div>

            {/* FOOTER */}
            <div className="editor-footer">
                <div className="footer-actions-left">
                    {eraId && canDelete() && (
                        <Button
                            variant="outline"
                            className="footer-btn"
                            style={{ borderColor: '#991b1b', color: '#fca5a5' }}
                            onClick={handleDelete}
                            disabled={submitting}
                        >
                            Delete Era
                        </Button>
                    )}
                    <Button
                        variant="secondary"
                        className="footer-btn"
                        onClick={() => onSuccess && onSuccess()}
                        disabled={submitting}
                    >
                        {eraId ? 'Back' : 'Cancel'}
                    </Button>
                </div>
                <div className="footer-actions-right">
                    <Button
                        variant={isRequestMode() ? 'primary' : 'primary'} // Original: .save (primary) or .request (primary-ish)
                        className={`footer-btn ${isRequestMode() ? 'request' : 'save'}`}
                        onClick={() => handleSave(false)}
                        disabled={submitting}
                    >
                        {isRequestMode() ? 'Request Update' : 'Save'}
                    </Button>
                    <Button
                        variant={isRequestMode() ? 'primary' : 'primary'}
                        className={`footer-btn ${isRequestMode() ? 'request' : 'save-close'}`}
                        onClick={() => handleSave(true)}
                        disabled={submitting}
                    >
                        {isRequestMode() ? 'Request & Close' : 'Save & Close'}
                    </Button>
                </div>
            </div>

            <SponsorManagerModal
                isOpen={isSponsorModalOpen}
                onClose={() => setIsSponsorModalOpen(false)}
                eraId={eraId}
                seasonYear={formData.season_year}
                registeredName={formData.registered_name}
                onUpdate={loadSponsorStats}
            />
        </div >
    );
}
