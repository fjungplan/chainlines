import { useState, useEffect, useRef } from 'react';
import { sponsorsApi } from '../../api/sponsors';
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
    const { isAdmin } = useAuth();

    // === STATE ===
    const [loading, setLoading] = useState(!!masterId);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [viewMode, setViewMode] = useState('MASTER'); // 'MASTER' or 'BRAND'

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
        source_notes: ''
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
            source_notes: brand.source_notes || ''
        });
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
            if (masterId) {
                await sponsorsApi.updateMaster(masterId, masterForm);
                if (shouldClose) onSuccess(); // Refresh list & close
                else setSubmitting(false);
            } else {
                await sponsorsApi.createMaster(masterForm);
                onSuccess(); // Close for now (or we could redirect to edit mode with returned ID)
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to save sponsor");
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
            if (currentBrand) {
                // Update
                await sponsorsApi.updateBrand(currentBrand.brand_id, brandForm);
            } else {
                // Create
                await sponsorsApi.addBrand(masterId, brandForm);
            }

            // Reload brands to reflect changes
            await loadMasterData();

            if (shouldClose) {
                setViewMode('MASTER');
            } else {
                setSubmitting(false);
                if (!currentBrand) {
                    // If we just created, ideally we switch to edit mode for it, 
                    // but reloading data might have lost our specific new ID reference easily.
                    // For safety/simplicity, we go back to Master on "Save & Close", 
                    // but for "Save" we might need to find the new brand. 
                    // Let's just go back to Master for now if it was a create, to be safe.
                    // Or keep form dirty? No, safer to go back.
                    setViewMode('MASTER');
                }
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to save brand");
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
                        <div className="form-row" style={{ marginBottom: '1.5rem', alignItems: 'center', height: '28px' }}>
                            <div style={{ flex: 1.5 }}>
                                <h3>Brand Details</h3>
                            </div>
                            <div style={{ flex: 1 }}>
                                <div className="header-color-picker full-width">
                                    <label>Color</label>
                                    <div className="color-inputs">
                                        <input
                                            type="color"
                                            value={brandForm.default_hex_color}
                                            onChange={e => handleBrandChange('default_hex_color', e.target.value)}
                                            title="Choose color"
                                        />
                                        <input
                                            type="text"
                                            value={brandForm.default_hex_color}
                                            onChange={e => handleBrandChange('default_hex_color', e.target.value)}
                                            pattern="^#[0-9A-Fa-f]{6}$"
                                            required
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="column-header">
                            <h3>Sponsor Details</h3>
                            {isAdmin() && (
                                <label className="protected-toggle">
                                    <input
                                        type="checkbox"
                                        checked={masterForm.is_protected}
                                        onChange={e => handleMasterChange('is_protected', e.target.checked)}
                                    />
                                    <span>Protected Record</span>
                                </label>
                            )}
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
                                    />
                                </div>

                                <div className="form-group" style={{ flex: 1, position: 'relative' }} ref={industryInputRef}>
                                    <label>Industry Sector</label>
                                    <input
                                        type="text"
                                        value={masterForm.industry_sector}
                                        onChange={e => handleMasterChange('industry_sector', e.target.value)}
                                        onFocus={() => setShowIndustryDropdown(true)}
                                        placeholder="Select or type..."
                                        className="industry-input"
                                        autoComplete="off"
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
                                />
                            </div>

                            <div className="form-group">
                                <label>Internal Notes</label>
                                <textarea
                                    value={masterForm.source_notes}
                                    onChange={e => handleMasterChange('source_notes', e.target.value)}
                                    rows={3}
                                />
                            </div>
                        </form>
                    ) : (
                        /* --- BRAND FORM --- */
                        <form onSubmit={(e) => { e.preventDefault(); }}>
                            <div className="form-row">
                                <div className="form-group" style={{ flex: 1.5 }}>
                                    <label>Brand Name * (e.g. Visma)</label>
                                    <input
                                        type="text"
                                        value={brandForm.brand_name}
                                        onChange={e => handleBrandChange('brand_name', e.target.value)}
                                        placeholder="e.g. Visma"
                                        required
                                    />
                                </div>

                                <div className="form-group" style={{ flex: 1 }}>
                                    <label>Display Name</label>
                                    <input
                                        type="text"
                                        value={brandForm.display_name}
                                        onChange={e => handleBrandChange('display_name', e.target.value)}
                                        placeholder="if different"
                                    />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Source URL</label>
                                <input
                                    type="url"
                                    value={brandForm.source_url}
                                    onChange={e => handleBrandChange('source_url', e.target.value)}
                                />
                            </div>

                            <div className="form-group">
                                <label>Internal Notes</label>
                                <textarea
                                    value={brandForm.source_notes}
                                    onChange={e => handleBrandChange('source_notes', e.target.value)}
                                    rows={3}
                                />
                            </div>
                        </form>
                    )}
                </div>

                {/* === RIGHT COLUMN (ALWAYS VISIBLE) === */}
                <div className="editor-column brands-column">
                    <div className="column-header">
                        <h3>Brand Identities</h3>
                        {masterId && (
                            <button className="secondary-btn small" onClick={handleAddBrand}>
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
                    onClick={handleBack} // Back logic handles 'Cancel' effectively
                    disabled={submitting}
                >
                    {isBrandMode ? 'Cancel' : 'Cancel'}
                </button>
                <div className="footer-actions-right">
                    <button
                        type="button"
                        className="footer-btn save"
                        onClick={() => isBrandMode ? handleSaveBrand(false) : handleSaveMaster(false)}
                        disabled={submitting}
                    >
                        Save
                    </button>
                    <button
                        type="button"
                        className="footer-btn save-close"
                        onClick={() => isBrandMode ? handleSaveBrand(true) : handleSaveMaster(true)}
                        disabled={submitting}
                    >
                        {isBrandMode ? 'Save & Close' : 'Save & Close'}
                    </button>
                </div>
            </div>
        </div>
    );
}
