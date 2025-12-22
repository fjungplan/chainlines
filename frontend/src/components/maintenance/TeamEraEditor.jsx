import { useState, useEffect } from 'react';
import { teamsApi } from '../../api/teams';
import { sponsorsApi } from '../../api/sponsors';
import { LoadingSpinner } from '../Loading';
import SponsorManagerModal from './SponsorManagerModal';
import './SponsorEditor.css'; // Reuse Sponsor style
import TeamEraBubbles from './TeamEraBubbles';
import { IOC_CODES } from '../../utils/iocCodes';
import { getTierName } from '../../utils/tierUtils';

export default function TeamEraEditor({ eraId, nodeId, onSuccess, onDelete }) {
    // State
    const [loading, setLoading] = useState(!!eraId);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [stats, setStats] = useState(null);

    const [formData, setFormData] = useState({
        season_year: new Date().getFullYear(),
        valid_from: '',
        registered_name: '',
        tier_level: 1,
        uci_code: '',
        country_code: ''
    });

    const [isSponsorModalOpen, setIsSponsorModalOpen] = useState(false);
    const [isCountryOpen, setIsCountryOpen] = useState(false);

    const [prefilledSponsors, setPrefilledSponsors] = useState([]);

    useEffect(() => {
        if (eraId) {
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
            if (eras && eras.length > 0) {
                // Find latest by season_year
                const sorted = eras.sort((a, b) => b.season_year - a.season_year);
                const latest = sorted[0];
                const nextYear = latest.season_year + 1;

                setFormData({
                    season_year: nextYear,
                    valid_from: `${nextYear}-01-01`,
                    registered_name: latest.registered_name,
                    tier_level: latest.tier_level,
                    uci_code: latest.uci_code || '',
                    country_code: latest.country_code || ''
                });

                // Fetch sponsors to pre-populate
                try {
                    const links = await sponsorsApi.getEraLinks(latest.era_id);
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
            if (!era) throw new Error("Era not found");

            setFormData({
                season_year: era.season_year,
                valid_from: era.valid_from ? era.valid_from.split('T')[0] : '',
                registered_name: era.registered_name,
                tier_level: era.tier_level,
                uci_code: era.uci_code || '',
                country_code: era.country_code || ''
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
                await teamsApi.updateTeamEra(eraId, payload);
            } else {
                const res = await teamsApi.createTeamEra(nodeId, payload);
                resultId = res.era_id;

                // Copy sponsors if pre-filled
                if (prefilledSponsors.length > 0) {
                    try {
                        const uniqueBrands = new Set();
                        // Filter duplicates just in case, though logically shouldn't be any
                        const sponsorPayload = prefilledSponsors
                            .filter(l => {
                                const bid = l.brand?.brand_id || l.brand_id;
                                if (uniqueBrands.has(bid)) return false;
                                uniqueBrands.add(bid);
                                return true;
                            })
                            .map(l => ({
                                brand_id: l.brand?.brand_id || l.brand_id,
                                rank_order: l.rank_order,
                                prominence_percent: l.prominence_percent,
                                hex_color_override: l.hex_color_override
                            }));
                        await sponsorsApi.replaceEraLinks(resultId, sponsorPayload);
                    } catch (spErr) {
                        console.error("Failed to copy sponsors", spErr);
                    }
                }

                if (onSuccess) onSuccess(resultId);
            }

            if (shouldClose) {
                if (onSuccess) onSuccess(); // Navigate back
            } else {
                setSubmitting(false);
                if (!eraId) {
                    // Stay on page: ideally reload data or switch ID
                    if (onSuccess) onSuccess(resultId);
                }
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to save era");
            setSubmitting(false);
        }
    };

    const handleDelete = async () => {
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
                    <button className="back-btn" onClick={() => onSuccess && onSuccess()} title="Back to Team">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                        </svg>
                    </button>
                    <h2>{eraId ? `Edit Era (Season): ${formData.season_year}` : 'Add New Era (Season)'}</h2>
                </div>
            </div>

            <div className="editor-split-view">
                {/* FORM */}
                <div className="editor-column details-column">
                    <div className="column-header">
                        <h3>Era (Season) Properties</h3>
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
                                />
                            </div>
                            <div className="form-group" style={{ flex: 2 }}>
                                <label>Registered Name *</label>
                                <input
                                    type="text"
                                    value={formData.registered_name}
                                    onChange={e => handleChange('registered_name', e.target.value)}
                                    required
                                />
                            </div>
                            <div className="form-group" style={{ flex: '0 0 100px' }}>
                                <label>UCI Code</label>
                                <input
                                    type="text"
                                    value={formData.uci_code}
                                    onChange={e => handleChange('uci_code', e.target.value)}
                                    maxLength={3}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group" style={{ flex: 2 }}>
                                <label>Tier Level *</label>
                                <select
                                    value={formData.tier_level}
                                    onChange={e => handleChange('tier_level', parseInt(e.target.value))}
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
                                />
                            </div>
                        </div>

                        {/* Sponsor Section */}
                        {(eraId || stats) && (
                            <div className="era-sponsors-section">
                                <div className="section-header">
                                    <label>Era Sponsors</label>
                                    {eraId ? (
                                        <button
                                            className="secondary-btn small"
                                            type="button"
                                            onClick={() => setIsSponsorModalOpen(true)}
                                        >
                                            Manage Sponsors
                                        </button>
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
                        <button className="secondary-btn small" onClick={() => handleEraSwitch('NEW')}>
                            + New Era
                        </button>
                    </div>
                    <TeamEraBubbles
                        nodeId={nodeId}
                        onEraSelect={handleEraSwitch}
                        onCreateEra={() => handleEraSwitch('NEW')}
                    />
                </div>
            </div>

            {/* FOOTER */}
            <div className="editor-footer">
                <div className="footer-actions-left">
                    {eraId && (
                        <button
                            type="button"
                            className="footer-btn"
                            style={{ borderColor: '#991b1b', color: '#fca5a5' }}
                            onClick={handleDelete}
                            disabled={submitting}
                        >
                            Delete Era
                        </button>
                    )}
                    <button
                        type="button"
                        className="footer-btn"
                        onClick={() => onSuccess && onSuccess()}
                        disabled={submitting}
                    >
                        {eraId ? 'Back' : 'Cancel'}
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

            <SponsorManagerModal
                isOpen={isSponsorModalOpen}
                onClose={() => setIsSponsorModalOpen(false)}
                eraId={eraId}
                seasonYear={formData.season_year}
                onUpdate={loadSponsorStats}
            />
        </div>
    );
}
