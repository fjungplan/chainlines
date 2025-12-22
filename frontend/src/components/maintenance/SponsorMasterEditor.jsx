import { useState, useEffect, useRef } from 'react';
import { sponsorsApi } from '../../api/sponsors';
import { editsApi } from '../../api/edits';
import { LoadingSpinner } from '../Loading';
import './SponsorEditor.css';
import { useAuth } from '../../contexts/AuthContext';

const INDUSTRIES = [
    "Financial Services", "Insurance", "Banking", "Telecommunications",
    "Automotive", "Retail", "Energy", "Construction",
    "Tourism", "Beverage", "Food", "Technology",
    "Logistics", "Healthcare", "Government/Region",
    "Gambling/Lottery", "Bicycles/Equipment", "Other"
];

export default function SponsorMasterEditor({ masterId, onClose, onSuccess }) {
    const { isAdmin, isModerator, isTrusted } = useAuth();

    // Determine Rights
    const canDirectEdit = isTrusted(); // Trusted, Moderator, Admin
    const showReasonField = !isModerator() && !isAdmin(); // Only hide for Mod/Admin

    // === STATE ===
    const [loading, setLoading] = useState(!!masterId);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [viewMode, setViewMode] = useState('MASTER'); // 'MASTER' or 'BRAND'
    const [reason, setReason] = useState(''); // For edit requests

    // Master Data
    const [masterForm, setMasterForm] = useState({
        legal_name: '',
        industry_sector: '',
        is_protected: false,
        source_url: '',
        source_notes: ''
    });

    // Brands List (Right Column)
    const [brands, setBrands] = useState([]);

    // Brand Data (Left Column when viewMode === 'BRAND')
    const [currentBrand, setCurrentBrand] = useState(null); // null = new brand
    const [brandForm, setBrandForm] = useState({
        brand_name: '',
        display_name: '',
        default_hex_color: '#ffffff',
        source_url: '',
        source_notes: '',
        is_protected: false // Added protection for brands
    });

    // UI Helpers
    const [showIndustryDropdown, setShowIndustryDropdown] = useState(false);
    const industryInputRef = useRef(null);

    // === INITIAL LOAD ===
    useEffect(() => {
        if (masterId) {
            loadMasterData();
        }
    }, [masterId]);

    // Click outside listener for dropdown
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (industryInputRef.current && !industryInputRef.current.contains(event.target)) {
                setShowIndustryDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const loadMasterData = async () => {
        setLoading(true);
        try {
            const data = await sponsorsApi.getMaster(masterId);
            setMasterForm({
                legal_name: data.legal_name,
                industry_sector: data.industry_sector || '',
                is_protected: data.is_protected,
                source_url: data.source_url || '',
                source_notes: data.source_notes || ''
            });
            setBrands(data.brands || []);
        } catch (err) {
            console.error("Failed to load master:", err);
            setError("Failed to load sponsor details");
        } finally {
            setLoading(false);
        }
    };

    // === HANDLERS: Navigation ===

    const handleBack = () => {
        if (viewMode === 'BRAND') {
            // "Up" navigation: Return to Master View
            setViewMode('MASTER');
            setError(null);
        } else {
            // "Back" navigation: Close Editor
            onClose();
        }
    };

    const handleSelectBrand = (brand) => {
        setCurrentBrand(brand);
        setBrandForm({
            brand_name: brand.brand_name,
            display_name: brand.display_name || '',
            default_hex_color: brand.default_hex_color,
            source_url: brand.source_url || '',
            source_notes: brand.source_notes || '',
            is_protected: brand.is_protected
        });
        setReason(''); // Reset reason
        setViewMode('BRAND');
        setError(null);
    };

    const handleAddBrand = () => {
        setCurrentBrand(null); // New mode
        setBrandForm({
            brand_name: '',
            display_name: '',
            default_hex_color: '#ffffff',
            source_url: '',
            source_notes: ''
        });
        setViewMode('BRAND');
        setError(null);
    };

    // === HANDLERS: Master ===

    const handleMasterChange = (field, value) => {
        setMasterForm(prev => ({ ...prev, [field]: value }));
    };

    const handleSaveMaster = async (shouldClose) => {
        setSubmitting(true);
        setError(null);
        try {
            // Reason Validation
            if (showReasonField && (!reason || reason.length < 10)) {
                throw new Error("Please provide a reason for this change (at least 10 characters).");
            }

            const payload = { ...masterForm, reason: reason }; // Always include reason if present

            let message = "";

            if (masterId) {
                // UPDATE - Use Edits API for Audit
                const requestData = {
                    master_id: masterId,
                    ...payload
                };
                await editsApi.updateSponsorMaster(masterId, requestData);
                message = canDirectEdit ? "Sponsor updated successfully" : "Update request submitted for moderation";

                if (shouldClose) onSuccess();
                else {
                    setSubmitting(false);
                    alert(message);
                    if (!canDirectEdit) onSuccess();
                }
            } else {
                // CREATE
                if (canDirectEdit) {
                    await sponsorsApi.createMaster(payload);
                    // Note: Reason lost here if sponsorsApi doesn't support it, but flow is smoother
                    onSuccess();
                } else {
                    await editsApi.createSponsorMaster(payload);
                    message = "Sponsor creation request submitted for moderation";
                    alert(message);
                    onSuccess();
                }
            }
        } catch (err) {
            setError(err.response?.data?.detail || err.message || "Failed to save sponsor");
            setSubmitting(false);
        }
    };

    // === HANDLERS: Brand ===

    const handleBrandChange = (field, value) => {
        setBrandForm(prev => ({ ...prev, [field]: value }));
    };

    const handleSaveBrand = async (shouldClose) => {
        setSubmitting(true);
        setError(null);
        try {
            // Reason Validation
            if (showReasonField && (!reason || reason.length < 10)) {
                throw new Error("Please provide a reason for this change (at least 10 characters).");
            }

            const payload = { ...brandForm, reason: reason };

            let message = "";

            if (currentBrand) {
                // Update - Use Edits API
                const requestData = {
                    brand_id: currentBrand.brand_id,
                    master_id: masterId,
                    ...payload
                };
                await editsApi.updateSponsorBrand(currentBrand.brand_id, requestData);
                message = canDirectEdit ? "Brand updated successfully" : "Brand update request submitted for moderation";

                if (canDirectEdit) await loadMasterData(); // Refresh list
                else alert(message);

            } else {
                // Create
                if (canDirectEdit) {
                    await sponsorsApi.addBrand(masterId, payload);
                    message = "Brand created successfully";
                    if (canDirectEdit) await loadMasterData();
                } else {
                    const requestData = {
                        master_id: masterId,
                        ...payload
                    };
                    await editsApi.createSponsorBrand(requestData);
                    message = "Brand creation request submitted for moderation";
                    alert(message);
                }
            }

            if (shouldClose) {
                setViewMode('MASTER');
                setReason('');
                if (canDirectEdit) await loadMasterData();
            } else {
                setSubmitting(false);
                if (!currentBrand && canDirectEdit) {
                    // Go back to Master list to refresh brands
                    setViewMode('MASTER');
                    setReason('');
                }
            }
        } catch (err) {
            setError(err.response?.data?.detail || err.message || "Failed to save brand");
            setSubmitting(false);
        }
    };

    // Filter industries
    const filteredIndustries = INDUSTRIES.filter(ind =>
        ind.toLowerCase().includes(masterForm.industry_sector.toLowerCase())
    );

    if (loading) return <div className="sponsor-inner-container"><LoadingSpinner /></div>;

    // === RENDER ===

    const isBrandMode = viewMode === 'BRAND';
    const headerTitle = isBrandMode
        ? (currentBrand ? 'Edit Brand Identity' : 'Add Brand Identity')
        : (masterId ? 'Edit Sponsor' : 'Create New Sponsor');

    // Protection Handling
    const isProtected = isBrandMode
        ? (brandForm.is_protected && !isModerator()) // Brand protected
        : (masterId && masterForm.is_protected && !isModerator()); // Master protected

    const saveBtnLabel = canDirectEdit ? "Save" : "Request Update";
    const saveCloseBtnLabel = canDirectEdit ? "Save & Close" : "Request & Close";

    return (
        <div className="sponsor-inner-container centered-editor-container">
            <div className="editor-header">
                <div className="header-left">
                    <button className="back-btn" onClick={handleBack} title={isBrandMode ? "Back to Sponsor" : "Back to List"}>
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                        </svg>
                    </button>
                    <h2>{headerTitle}</h2>
                </div>
            </div>

            <div className="editor-split-view">
                {/* === LEFT COLUMN (SWAPPABLE) === */}
                <div className="editor-column details-column">
                    {/* Header Varies by Mode for Alignment */}
                    {isBrandMode ? (
                        <div className="column-header">
                            <h3>Brand Details</h3>
                            {isModerator() && (
                                <label className="protected-toggle">
                                    <input
                                        type="checkbox"
                                        checked={brandForm.is_protected}
                                        onChange={e => handleBrandChange('is_protected', e.target.checked)}
                                    />
                                    <span>Protected Record</span>
                                </label>
                            )}
                            {isProtected && <span className="badge badge-warning">Protected (Read Only)</span>}
                        </div>
                    ) : (
                        <div className="column-header">
                            <h3>Sponsor Details</h3>
                            {isModerator() && (
                                <label className="protected-toggle">
                                    <input
                                        type="checkbox"
                                        checked={masterForm.is_protected}
                                        onChange={e => handleMasterChange('is_protected', e.target.checked)}
                                    />
                                    <span>Protected Record</span>
                                </label>
                            )}
                            {isProtected && <span className="badge badge-warning">Protected (Read Only)</span>}
                        </div>
                    )}

                    {error && <div className="error-banner">{error}</div>}

                    {!isBrandMode ? (
                        /* --- MASTER FORM --- */
                        <form onSubmit={(e) => { e.preventDefault(); }}>
                            <div className="form-row">
                                <div className="form-group" style={{ flex: 1.5 }}>
                                    <label>Legal Name *</label>
                                    <input
                                        type="text"
                                        value={masterForm.legal_name}
                                        onChange={e => handleMasterChange('legal_name', e.target.value)}
                                        required
                                        readOnly={isProtected}
                                    />
                                </div>

                                <div className="form-group" style={{ flex: 1, position: 'relative' }} ref={industryInputRef}>
                                    <label>Industry Sector</label>
                                    <input
                                        type="text"
                                        value={masterForm.industry_sector}
                                        onChange={e => handleMasterChange('industry_sector', e.target.value)}
                                        onFocus={() => !isProtected && setShowIndustryDropdown(true)}
                                        placeholder="Select or type..."
                                        className="industry-input"
                                        autoComplete="off"
                                        readOnly={isProtected}
                                    />
                                    {showIndustryDropdown && filteredIndustries.length > 0 && (
                                        <ul className="custom-dropdown-list">
                                            {filteredIndustries.map(ind => (
                                                <li key={ind} onClick={() => {
                                                    handleMasterChange('industry_sector', ind);
                                                    setShowIndustryDropdown(false);
                                                }}>
                                                    {ind}
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Source URL</label>
                                <input
                                    type="url"
                                    value={masterForm.source_url}
                                    onChange={e => handleMasterChange('source_url', e.target.value)}
                                    readOnly={isProtected}
                                />
                            </div>

                            <div className="form-group">
                                <label>Internal Notes</label>
                                <textarea
                                    value={masterForm.source_notes}
                                    onChange={e => handleMasterChange('source_notes', e.target.value)}
                                    rows={3}
                                    readOnly={isProtected}
                                />
                            </div>
                        </form>
                    ) : (
                        /* --- BRAND FORM --- */
                        <form onSubmit={(e) => { e.preventDefault(); }}>
                            {/* Color Picker moved here for consistency */}

                            <div className="form-row">
                                <div className="form-group" style={{ flex: 1.5 }}>
                                    <label>Brand Name * (e.g. Visma)</label>
                                    <input
                                        type="text"
                                        value={brandForm.brand_name}
                                        onChange={e => handleBrandChange('brand_name', e.target.value)}
                                        placeholder="e.g. Visma"
                                        required
                                        readOnly={isProtected}
                                    />
                                </div>

                                <div className="form-group" style={{ flex: 1 }}>
                                    <label>Display Name</label>
                                    <input
                                        type="text"
                                        value={brandForm.display_name}
                                        onChange={e => handleBrandChange('display_name', e.target.value)}
                                        placeholder="if different"
                                        readOnly={isProtected}
                                    />
                                </div>
                            </div>

                            <div className="form-row">
                                <div className="form-group" style={{ flex: 1 }}>
                                    <label>Source URL</label>
                                    <input
                                        type="url"
                                        value={brandForm.source_url}
                                        onChange={e => handleBrandChange('source_url', e.target.value)}
                                        readOnly={isProtected}
                                    />
                                </div>
                                <div className="form-group" style={{ width: '240px' }}>
                                    <label>Brand Color</label>
                                    <div className="color-input-group">
                                        <div className="color-preview-wrapper" style={{ backgroundColor: brandForm.default_hex_color }}>
                                            <input
                                                type="color"
                                                value={brandForm.default_hex_color}
                                                onChange={e => handleBrandChange('default_hex_color', e.target.value)}
                                                title="Choose color"
                                                disabled={isProtected}
                                                style={{ position: 'absolute', top: '-50%', left: '-50%', width: '200%', height: '200%', padding: 0, margin: 0, border: 'none', cursor: 'pointer', opacity: 0 }}
                                            />
                                        </div>
                                        <input
                                            type="text"
                                            value={brandForm.default_hex_color}
                                            onChange={e => handleBrandChange('default_hex_color', e.target.value)}
                                            pattern="^#[0-9A-Fa-f]{6}$"
                                            required
                                            readOnly={isProtected}
                                            style={{ flex: 1, fontFamily: 'monospace' }}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Internal Notes</label>
                                <textarea
                                    value={brandForm.source_notes}
                                    onChange={e => handleBrandChange('source_notes', e.target.value)}
                                    rows={3}
                                    readOnly={isProtected}
                                />
                            </div>
                        </form>
                    )}

                    {/* REASON FIELD FOR REQUESTS */}
                    {showReasonField && (
                        <div className="form-group reason-group" style={{ marginTop: '1rem' }}>
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
                </div>

                {/* === RIGHT COLUMN (ALWAYS VISIBLE) === */}
                <div className="editor-column brands-column">
                    <div className="column-header">
                        <h3>Brand Identities</h3>
                        {masterId && (
                            <button className="secondary-btn small" onClick={handleAddBrand} disabled={!isBrandMode && isProtected && !isModerator()}>
                                + Add
                            </button>
                        )}
                    </div>

                    {!masterId ? (
                        <div className="empty-panel">
                            <p>Save sponsor details first to add brand identities.</p>
                        </div>
                    ) : (
                        <div className="brands-list-container">
                            {brands.length === 0 ? (
                                <p className="empty-text">No brands recorded.</p>
                            ) : (
                                <div className="brands-list">
                                    {brands.map(brand => {
                                        const isActive = isBrandMode && currentBrand?.brand_id === brand.brand_id;
                                        return (
                                            <div
                                                key={brand.brand_id}
                                                className={`brand-item ${isActive ? 'active' : ''}`}
                                                onClick={() => handleSelectBrand(brand)}
                                            >
                                                <div className="brand-color" style={{ backgroundColor: brand.default_hex_color }}></div>
                                                <div className="brand-info">
                                                    <div className="brand-name">{brand.brand_name}</div>
                                                    {brand.display_name && <div className="brand-display">{brand.display_name}</div>}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* === FOOTER (CONTEXT AWARE) === */}
            <div className="editor-footer">
                <button
                    type="button"
                    className="footer-btn cancel"
                    onClick={handleBack}
                    disabled={submitting}
                >
                    Cancel
                </button>
                <div className="footer-actions-right">
                    {!isProtected && (
                        <>
                            <button
                                type="button"
                                className="footer-btn save"
                                onClick={() => isBrandMode ? handleSaveBrand(false) : handleSaveMaster(false)}
                                disabled={submitting}
                            >
                                {saveBtnLabel}
                            </button>
                            <button
                                type="button"
                                className="footer-btn save-close"
                                onClick={() => isBrandMode ? handleSaveBrand(true) : handleSaveMaster(true)}
                                disabled={submitting}
                            >
                                {saveCloseBtnLabel}
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
