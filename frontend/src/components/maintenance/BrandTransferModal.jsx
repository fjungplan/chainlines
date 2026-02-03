import { useState, useEffect } from 'react';
import { sponsorsApi } from '../../api/sponsors';
import { editsApi } from '../../api/edits';
import { LoadingSpinner } from '../Loading';
import { useAuth } from '../../contexts/AuthContext';
import Button from '../common/Button';
import './SponsorEditor.css';

/**
 * Modal for transferring SponsorBrands from a source sponsor to the current receiving sponsor.
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether the modal is open.
 * @param {string} props.receivingMasterId - The master_id of the sponsor receiving the brands.
 * @param {string} props.receivingMasterName - Name of the receiving sponsor for display.
 * @param {Function} props.onClose - Callback to close the modal.
 * @param {Function} props.onSuccess - Callback after successful transfer.
 */
export default function BrandTransferModal({ isOpen, receivingMasterId, receivingMasterName, onClose, onSuccess }) {
    const { isTrusted, isAdmin, isModerator } = useAuth();
    const canDirectEdit = isTrusted() || isAdmin() || isModerator();

    // Steps: 'search' -> 'select' -> 'confirm'
    const [step, setStep] = useState('search');

    // Search State
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);
    const [selectedSourceSponsor, setSelectedSourceSponsor] = useState(null);

    // Brand Selection State
    const [sourceBrands, setSourceBrands] = useState([]);
    const [selectedBrandIds, setSelectedBrandIds] = useState(new Set());
    const [brandsLoading, setBrandsLoading] = useState(false);

    // Submission State
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);
    const [reason, setReason] = useState('');

    const showReasonField = !isModerator() && !isAdmin();

    // Reset state when modal opens
    useEffect(() => {
        if (isOpen) {
            setStep('search');
            setSearchQuery('');
            setSearchResults([]);
            setSelectedSourceSponsor(null);
            setSourceBrands([]);
            setSelectedBrandIds(new Set());
            setError(null);
            setReason('');
        }
    }, [isOpen]);

    // Debounced search for source sponsors
    useEffect(() => {
        if (searchQuery.length < 2) {
            setSearchResults([]);
            return;
        }
        const timer = setTimeout(async () => {
            setSearchLoading(true);
            try {
                const res = await sponsorsApi.searchMasters(searchQuery, 15);
                // Filter out the receiving sponsor itself
                const filtered = (res.items || res).filter(s => s.master_id !== receivingMasterId);
                setSearchResults(filtered);
            } catch (err) {
                console.error("Search failed:", err);
            } finally {
                setSearchLoading(false);
            }
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery, receivingMasterId]);

    // Load brands when a source sponsor is selected
    useEffect(() => {
        if (!selectedSourceSponsor) return;
        const loadBrands = async () => {
            setBrandsLoading(true);
            try {
                const master = await sponsorsApi.getMaster(selectedSourceSponsor.master_id);
                setSourceBrands(master.brands || []);
            } catch (err) {
                console.error("Failed to load brands:", err);
                setError("Could not load brands for the selected sponsor.");
            } finally {
                setBrandsLoading(false);
            }
        };
        loadBrands();
        setStep('select');
    }, [selectedSourceSponsor]);

    const handleSelectSource = (sponsor) => {
        setSelectedSourceSponsor(sponsor);
        setSelectedBrandIds(new Set());
        setError(null);
    };

    const toggleBrandSelection = (brandId) => {
        setSelectedBrandIds(prev => {
            const next = new Set(prev);
            if (next.has(brandId)) {
                next.delete(brandId);
            } else {
                next.add(brandId);
            }
            return next;
        });
    };

    const handleConfirmStep = () => {
        if (selectedBrandIds.size === 0) {
            setError("Please select at least one brand to transfer.");
            return;
        }
        setError(null);
        setStep('confirm');
    };

    const handleDeleteSource = async () => {
        setSubmitting(true);
        try {
            await sponsorsApi.deleteMaster(selectedSourceSponsor.master_id);
            if (onSuccess) onSuccess();
            onClose();
        } catch (err) {
            console.error("Delete failed:", err);
            setError("Could not delete sponsor. It may have been modified.");
            setSubmitting(false);
        }
    };

    const handleTransfer = async () => {
        if (showReasonField && reason.length < 10) {
            setError("Please provide a reason for this change (at least 10 characters).");
            return;
        }

        setSubmitting(true);
        setError(null);

        try {
            const selectedBrandsData = sourceBrands.filter(b => selectedBrandIds.has(b.brand_id));

            // Submit one edit per brand (UPDATE to change master_id)
            for (const brand of selectedBrandsData) {
                const payload = {
                    master_id: receivingMasterId,
                    reason: reason
                };
                await editsApi.updateSponsorBrand(brand.brand_id, payload);
            }

            // Check if we emptied the source sponsor
            if (selectedBrandIds.size === sourceBrands.length) {
                setStep('delete_prompt');
                setSubmitting(false);
            } else {
                if (onSuccess) onSuccess();
                onClose();
            }
        } catch (err) {
            console.error("Transfer failed:", err);
            let errorMessage = "Transfer failed.";
            const detail = err.response?.data?.detail;
            if (typeof detail === 'string') {
                errorMessage = detail;
            } else if (Array.isArray(detail) && detail.length > 0) {
                errorMessage = detail.map(e => e.msg || JSON.stringify(e)).join(', ');
            } else if (err.message) {
                errorMessage = err.message;
            }
            setError(errorMessage);
            setSubmitting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="editor-overlay" onClick={onClose}>
            <div className="editor-modal" style={{ maxWidth: '600px', maxHeight: '80vh' }} onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div className="editor-header">
                    <div className="header-left">
                        <h2>Import Brands</h2>
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
                                Search for the sponsor you want to import brands FROM into <strong style={{ color: '#fff' }}>{receivingMasterName}</strong>.
                            </p>
                            <div className="form-group">
                                <label>Search Sponsors</label>
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
                                    {searchResults.map(sponsor => (
                                        <div
                                            key={sponsor.master_id}
                                            className="brand-item"
                                            onClick={() => handleSelectSource(sponsor)}
                                        >
                                            <div className="brand-info">
                                                <div className="brand-name">{sponsor.legal_name}</div>
                                                <div className="brand-display">{sponsor.industry_sector || 'Unknown Industry'}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Step 2: Select Brands */}
                    {step === 'select' && (
                        <div>
                            <p style={{ color: '#a0aec0', marginBottom: '0.5rem' }}>
                                Select brands to import from <strong style={{ color: '#fff' }}>{selectedSourceSponsor?.legal_name}</strong>:
                            </p>
                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => { setStep('search'); setSelectedSourceSponsor(null); setSourceBrands([]); }}
                                style={{ marginBottom: '1rem' }}
                            >
                                ← Change Source Sponsor
                            </Button>

                            {brandsLoading && <LoadingSpinner />}
                            {!brandsLoading && sourceBrands.length === 0 && (
                                <div className="empty-panel">No brands found for this sponsor.</div>
                            )}
                            {!brandsLoading && sourceBrands.length > 0 && (
                                <div className="brands-list">
                                    {sourceBrands.map(brand => (
                                        <label
                                            key={brand.brand_id}
                                            className={`brand-item ${selectedBrandIds.has(brand.brand_id) ? 'active' : ''}`}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={selectedBrandIds.has(brand.brand_id)}
                                                onChange={() => toggleBrandSelection(brand.brand_id)}
                                                style={{ marginRight: '0.75rem' }}
                                            />
                                            <div
                                                className="brand-color-swatch"
                                                style={{
                                                    width: '20px',
                                                    height: '20px',
                                                    backgroundColor: brand.default_hex_color || '#888',
                                                    borderRadius: '3px',
                                                    marginRight: '0.75rem',
                                                    border: '1px solid #555'
                                                }}
                                            />
                                            <div className="brand-info">
                                                <div className="brand-name">{brand.brand_name}</div>
                                                <div className="brand-display">{brand.display_name || ''}</div>
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
                                You are about to transfer <strong style={{ color: '#fff' }}>{selectedBrandIds.size}</strong> brand(s) from
                                <strong style={{ color: '#fff' }}> {selectedSourceSponsor?.legal_name}</strong> to <strong style={{ color: '#fff' }}>{receivingMasterName}</strong>.
                            </p>
                            <ul style={{ color: '#e2e8f0', marginBottom: '1rem', paddingLeft: '1.5rem' }}>
                                {sourceBrands.filter(b => selectedBrandIds.has(b.brand_id)).map(brand => (
                                    <li key={brand.brand_id}>
                                        <span style={{
                                            display: 'inline-block',
                                            width: '12px',
                                            height: '12px',
                                            backgroundColor: brand.default_hex_color || '#888',
                                            borderRadius: '2px',
                                            marginRight: '0.5rem',
                                            verticalAlign: 'middle'
                                        }} />
                                        {brand.brand_name}
                                    </li>
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

                            <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => setStep('select')}
                            >
                                ← Back to Selection
                            </Button>
                        </div>
                    )}

                    {/* Step 4: Delete Prompt */}
                    {step === 'delete_prompt' && (
                        <div>
                            <div style={{ textAlign: 'center', padding: '1rem 0' }}>
                                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
                                <h3 style={{ margin: '0 0 1rem 0' }}>Sponsor Cleanup</h3>
                                <p style={{ color: '#e2e8f0', marginBottom: '1.5rem', fontSize: '1.1rem' }}>
                                    The source sponsor <strong>'{selectedSourceSponsor?.legal_name}'</strong> is now empty.
                                    <br />
                                    Would you like to delete it?
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="editor-footer" style={{ padding: '0.75rem 1.5rem' }}>
                    <div className="footer-actions-left">
                        {step !== 'delete_prompt' && (
                            <Button variant="secondary" onClick={onClose} disabled={submitting}>Cancel</Button>
                        )}
                        {step === 'delete_prompt' && (
                            <Button variant="secondary" onClick={() => { if (onSuccess) onSuccess(); onClose(); }} disabled={submitting}>
                                No, Keep Empty
                            </Button>
                        )}
                    </div>
                    <div className="footer-actions-right">
                        {step === 'select' && (
                            <Button variant="primary" onClick={handleConfirmStep} disabled={selectedBrandIds.size === 0}>
                                Review Import ({selectedBrandIds.size})
                            </Button>
                        )}
                        {step === 'confirm' && (
                            <Button variant="primary" onClick={handleTransfer} disabled={submitting}>
                                {submitting ? 'Submitting...' : (canDirectEdit ? 'Confirm Import' : 'Request Import')}
                            </Button>
                        )}
                        {step === 'delete_prompt' && (
                            <Button variant="danger" onClick={handleDeleteSource} disabled={submitting}>
                                Yes, Delete Empty Sponsor
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
