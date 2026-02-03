import { useState, useEffect } from 'react';
import { sponsorsApi } from '../../api/sponsors';
import { LoadingSpinner } from '../Loading';
import Button from '../common/Button';
import './SponsorEditor.css';

/**
 * Modal for merging one SponsorBrand into another.
 * Destructive operation for the source brand.
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen
 * @param {Object} props.sourceBrand - The brand being merged away { brand_id, brand_name, master_id, default_hex_color }
 * @param {Function} props.onClose
 * @param {Function} props.onSuccess
 */
export default function BrandMergeModal({ isOpen, sourceBrand, onClose, onSuccess }) {
    // Steps: 'search' -> 'confirm'
    const [step, setStep] = useState('search');

    // Search State
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);
    const [targetBrand, setTargetBrand] = useState(null);

    // Submission State
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    // Reset loop
    useEffect(() => {
        if (isOpen) {
            setStep('search');
            setSearchQuery('');
            setSearchResults([]);
            setTargetBrand(null);
            setError(null);
            setSubmitting(false);
        }
    }, [isOpen]);

    // Search Logic
    useEffect(() => {
        if (searchQuery.length < 2) {
            setSearchResults([]);
            return;
        }

        const timer = setTimeout(async () => {
            setSearchLoading(true);
            try {
                // Search Brands directly
                const res = await sponsorsApi.searchBrands(searchQuery, 15);
                const items = res.items || res;

                // Filter out self
                const filtered = items.filter(b => b.brand_id !== sourceBrand?.brand_id);
                setSearchResults(filtered);
            } catch (err) {
                console.error("Search failed:", err);
            } finally {
                setSearchLoading(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [searchQuery, sourceBrand]);

    const handleSelectTarget = (brand) => {
        setTargetBrand(brand);
        setStep('confirm');
        setError(null);
    };

    const handleMerge = async () => {
        if (!sourceBrand || !targetBrand) return;

        setSubmitting(true);
        setError(null);

        try {
            await sponsorsApi.mergeBrand(sourceBrand.brand_id, targetBrand.brand_id);
            if (onSuccess) onSuccess();
            onClose();
        } catch (err) {
            console.error("Merge failed:", err);
            setError(err.response?.data?.detail || "Merge failed. Please try again.");
            setSubmitting(false);
        }
    };

    if (!isOpen || !sourceBrand) return null;

    return (
        <div className="editor-overlay" onClick={onClose}>
            <div className="editor-modal" style={{ maxWidth: '600px' }} onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div className="editor-header" style={{ borderBottom: '1px solid #444', padding: '1rem 1.5rem' }}>
                    <div className="header-left">
                        <h2 style={{ fontSize: '1.25rem', margin: 0 }}>Merge Brand</h2>
                    </div>
                </div>

                {/* Body */}
                <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1, minHeight: '300px' }}>
                    {error && <div className="error-banner">{error}</div>}

                    {step === 'search' && (
                        <div>
                            <p style={{ color: '#a0aec0', marginBottom: '1rem' }}>
                                You are merging <strong style={{ color: '#fed7aa' }}>{sourceBrand.brand_name}</strong>.
                                <br />
                                All links will be moved to the target brand, and this source brand will be deleted.
                            </p>

                            <div className="form-group">
                                <label>Search Target Brand</label>
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Search brands..."
                                    autoFocus
                                />
                            </div>

                            {searchLoading && <LoadingSpinner />}

                            {!searchLoading && searchResults.length > 0 && (
                                <div className="brands-list">
                                    {searchResults.map(brand => (
                                        <div
                                            key={brand.brand_id}
                                            className="brand-item"
                                            onClick={() => handleSelectTarget(brand)}
                                        >
                                            <div className="brand-color" style={{ backgroundColor: brand.default_hex_color }}></div>
                                            <div className="brand-info">
                                                <div className="brand-name">{brand.brand_name}</div>
                                                {brand.display_name && <div className="brand-display">{brand.display_name}</div>}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {step === 'confirm' && (
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔀</div>
                            <h3>Confirm Merge</h3>

                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '1rem',
                                margin: '2rem 0',
                                padding: '1rem',
                                background: '#1e293b',
                                borderRadius: '8px'
                            }}>
                                <span style={{ color: '#fca5a5' }}>{sourceBrand.brand_name}</span>
                                <span style={{ color: '#94a3b8' }}>➔</span>
                                <span style={{ color: '#86efac', fontWeight: 'bold' }}>{targetBrand.brand_name}</span>
                            </div>

                            <p style={{ color: '#e2e8f0', fontSize: '0.9rem' }}>
                                This action is <strong>irreversible</strong>.
                                <br />
                                Any overlapping eras will combine prominence and keep the best rank.
                            </p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="editor-footer" style={{ padding: '0.75rem 1.5rem' }}>
                    <div className="footer-actions-left">
                        <Button variant="secondary" onClick={onClose} disabled={submitting}>Cancel</Button>
                        {step === 'confirm' && (
                            <Button variant="secondary" onClick={() => setStep('search')} disabled={submitting}>Back</Button>
                        )}
                    </div>
                    <div className="footer-actions-right">
                        {step === 'confirm' && (
                            <Button variant="danger" onClick={handleMerge} disabled={submitting}>
                                {submitting ? 'Merging...' : 'Confirm Merge'}
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
