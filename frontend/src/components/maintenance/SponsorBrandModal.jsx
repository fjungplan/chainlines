import { useState, useEffect } from 'react';
import { sponsorsApi } from '../../api/sponsors';
import './SponsorEditor.css';

export default function SponsorBrandModal({ masterId, brand, onClose, onSuccess }) {
    // Keep 'Modal' filename for compatibility but it's now a full page editor
    const [formData, setFormData] = useState({
        brand_name: '',
        display_name: '',
        default_hex_color: '#ffffff',
        source_url: '',
        source_notes: ''
    });

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (brand) {
            setFormData({
                brand_name: brand.brand_name,
                display_name: brand.display_name || '',
                default_hex_color: brand.default_hex_color,
                source_url: brand.source_url || '',
                source_notes: brand.source_notes || ''
            });
        }
    }, [brand]);

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSave = async () => {
        setSubmitting(true);
        setError(null);
        try {
            if (brand) {
                await sponsorsApi.updateBrand(brand.brand_id, formData);
            } else {
                await sponsorsApi.addBrand(masterId, formData);
            }
            onSuccess();
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to save brand");
            setSubmitting(false);
        }
    };

    return (
        <div className="sponsor-inner-container editor-full-page">
            <div className="editor-header">
                <div className="header-left">
                    <button className="back-btn" onClick={onClose} title="Back to Sponsor">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                        </svg>
                    </button>
                    <h2>{brand ? 'Edit Brand Identity' : 'Add Brand Identity'}</h2>
                </div>
            </div>

            <div className="editor-column" style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
                {error && <div className="error-banner">{error}</div>}

                <form onSubmit={(e) => { e.preventDefault(); handleSave(); }}>
                    <div className="form-group">
                        <label>Brand Name * (e.g. Visma)</label>
                        <input
                            type="text"
                            value={formData.brand_name}
                            onChange={e => handleChange('brand_name', e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Display Name (optional)</label>
                        <input
                            type="text"
                            value={formData.display_name}
                            onChange={e => handleChange('display_name', e.target.value)}
                            placeholder="e.g. Team Visma (if different)"
                        />
                    </div>

                    <div className="form-group">
                        <label>Default Color *</label>
                        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                            <input
                                type="color"
                                value={formData.default_hex_color}
                                onChange={e => handleChange('default_hex_color', e.target.value)}
                                style={{ width: '50px', padding: 0, border: 'none', height: '40px', cursor: 'pointer' }}
                            />
                            <input
                                type="text"
                                value={formData.default_hex_color}
                                onChange={e => handleChange('default_hex_color', e.target.value)}
                                pattern="^#[0-9A-Fa-f]{6}$"
                                required
                                style={{ width: '120px' }}
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
                        onClick={handleSave}
                        disabled={submitting}
                    >
                        Save Brand
                    </button>
                </div>
            </div>
        </div>
    );
}
