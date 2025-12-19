import { useState, useEffect } from 'react';
import { sponsorsApi } from '../../api/sponsors';
import { LoadingSpinner } from '../Loading';
import './SponsorManagerModal.css';

export default function SponsorManagerModal({ isOpen, onClose, eraId, onUpdate }) {
    if (!isOpen) return null;

    const [links, setLinks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Add Mode
    const [isAdding, setIsAdding] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    // Form for new link
    const [selectedBrand, setSelectedBrand] = useState(null);
    const [rankOrder, setRankOrder] = useState(1);
    const [prominence, setProminence] = useState(50);
    const [colorOverride, setColorOverride] = useState('#ffffff');
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (eraId) loadLinks();
    }, [eraId]);

    const loadLinks = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await sponsorsApi.getEraLinks(eraId);
            // Sort by Prominence Percent (Descending)
            setLinks(data.sort((a, b) => b.prominence_percent - a.prominence_percent));
        } catch (err) {
            setError("Failed to load sponsors");
        } finally {
            setLoading(false);
        }
    };

    // Search Brands
    useEffect(() => {
        const delaySearch = setTimeout(async () => {
            if (searchTerm.length >= 2) {
                try {
                    const results = await sponsorsApi.searchBrands(searchTerm);
                    setSearchResults(results);
                } catch (e) {
                    console.error(e);
                }
            } else {
                setSearchResults([]);
            }
        }, 500);
        return () => clearTimeout(delaySearch);
    }, [searchTerm]);

    const handleAddClick = () => {
        setIsAdding(true);
        // Default rank order to next available (backend requirement)
        const nextRank = links.length > 0 ? Math.max(...links.map(l => l.rank_order)) + 1 : 1;
        setRankOrder(nextRank);
        setProminence(50);
        setSelectedBrand(null);
        setSearchTerm('');
    };

    const handleSelectBrand = (brand) => {
        setSelectedBrand(brand);
        setColorOverride(brand.default_hex_color);
        setSearchTerm(brand.brand_name); // Visual feedback
        setSearchResults([]); // Hide list
    };

    const calculateTotalProminence = () => {
        return links.reduce((sum, link) => sum + link.prominence_percent, 0);
    };

    const handleSaveLink = async () => {
        if (!selectedBrand) return;
        setSubmitting(true);
        setError(null);
        try {
            await sponsorsApi.linkSponsor(eraId, {
                brand_id: selectedBrand.brand_id,
                rank_order: rankOrder,
                prominence_percent: prominence,
                hex_color_override: colorOverride
            });
            await loadLinks();
            setIsAdding(false);
            if (onUpdate) onUpdate();
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to add sponsor");
        } finally {
            setSubmitting(false);
        }
    };

    const handleRemoveLink = async (linkId) => {
        if (!window.confirm("Remove this sponsor?")) return;
        try {
            await sponsorsApi.removeLink(linkId);
            await loadLinks();
            if (onUpdate) onUpdate();
        } catch (err) {
            setError("Failed to remove sponsor");
        }
    };

    const totalProminence = calculateTotalProminence();

    return (
        <div className="modal-overlay">
            <div className="modal-content sponsor-manager-modal">
                <div className="modal-header">
                    <h2>Manage Sponsors</h2>
                    <button className="close-btn" onClick={onClose}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18 6L6 18M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="modal-body">
                    {/* LEFT COLUMN: List */}
                    <div className="modal-column-left">
                        <div className="prominence-bar">
                            <div className="bar-track">
                                <div className="bar-fill" style={{ width: `${Math.min(totalProminence, 100)}%`, background: totalProminence > 100 ? '#ef4444' : '#10b981' }}></div>
                            </div>
                            <span>Total Prominence: {totalProminence}%</span>
                        </div>

                        {loading ? <LoadingSpinner /> : (
                            <div className="sponsors-list">
                                <table className="mini-table">
                                    <thead>
                                        <tr>
                                            <th>Rank</th>
                                            <th>Brand</th>
                                            <th>%</th>
                                            <th></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {links.map(link => (
                                            <tr key={link.link_id}>
                                                <td>{link.rank_order}</td>
                                                <td>
                                                    <div className="brand-cell">
                                                        <div className="color-dot" style={{ background: link.hex_color_override || link.brand?.default_hex_color }}></div>
                                                        {link.brand?.brand_name}
                                                    </div>
                                                </td>
                                                <td>{link.prominence_percent}%</td>
                                                <td>
                                                    <button className="icon-btn delete" onClick={() => handleRemoveLink(link.link_id)} title="Remove Sponsor">
                                                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6" />
                                                        </svg>
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>

                    {/* RIGHT COLUMN: Add Form */}
                    <div className="modal-column-right">
                        {error && <div className="error-banner">{error}</div>}

                        <div className="add-sponsor-container">
                            <h4>Add Sponsor</h4>
                            <div className="add-sponsor-form">
                                <div className="form-group search-group">
                                    <label>Search Brand *</label>
                                    <input
                                        type="text"
                                        value={searchTerm}
                                        onChange={e => setSearchTerm(e.target.value)}
                                        placeholder="Type brand name..."
                                    />
                                    {searchResults.length > 0 && (
                                        <ul className="dropdown-results">
                                            {searchResults.map(b => (
                                                <li key={b.brand_id} onClick={() => handleSelectBrand(b)}>
                                                    {b.brand_name}
                                                </li>
                                            ))}
                                        </ul>
                                    )}
                                </div>

                                <div className="form-group">
                                    <label>Prominence % *</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <input
                                            type="number"
                                            min="1"
                                            max="100"
                                            value={prominence}
                                            onChange={e => setProminence(parseInt(e.target.value))}
                                            style={{ flex: 1 }}
                                        />
                                        <span style={{ color: '#666', fontSize: '0.9rem' }}>%</span>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label>Hex Color</label>
                                    <div className="color-input-group">
                                        <div className="color-preview-wrapper" style={{ background: colorOverride }}>
                                            <input
                                                type="color"
                                                value={colorOverride}
                                                onChange={e => setColorOverride(e.target.value)}
                                                title="Choose color"
                                            />
                                        </div>
                                        <input
                                            type="text"
                                            value={colorOverride}
                                            onChange={e => setColorOverride(e.target.value)}
                                            placeholder="#RRGGBB"
                                        />
                                    </div>
                                </div>
                                <div className="form-actions" style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid #444' }}>
                                    <button
                                        className="footer-btn"
                                        onClick={() => {
                                            setSelectedBrand(null);
                                            setSearchTerm('');
                                            // Reset other fields if desired, but keeping previous values is often UX-friendly
                                        }}
                                    >
                                        Clear
                                    </button>
                                    <button
                                        className="footer-btn save"
                                        onClick={handleSaveLink}
                                        disabled={submitting || !selectedBrand}
                                        title={!selectedBrand ? "Select a brand first" : "Add Link"}
                                    >
                                        {submitting ? 'Adding...' : 'Add Link'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
