import { useState, useEffect } from 'react';
import './SponsorEditor.css';

export default function SponsorBrandForm({ brand, onSave, onCancel }) {
    const [formData, setFormData] = useState({
        brand_name: '',
        display_name: '',
        default_hex_color: '#ffffff',
        source_url: '',
        source_notes: ''
    });

    useEffect(() => {
        if (brand) {
            setFormData({
                brand_name: brand.brand_name || '',
                display_name: brand.display_name || '',
                default_hex_color: brand.default_hex_color || '#ffffff',
                source_url: brand.source_url || '',
                source_notes: brand.source_notes || ''
            });
        } else {
            // New Brand defaults
            setFormData({
                brand_name: '',
                display_name: '',
                default_hex_color: '#ffffff',
                source_url: '',
                source_notes: ''
            });
        }
    }, [brand]);

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    // Expose submit handler for the parent footer to call, or use internal form submit
    // But since the footer is in the parent, the parent needs to trigger this.
    // Actually, distinct form in child is tricky with parent footer.
    // Standard React pattern: Parent passes "ref" or "save trigger".
    // OR simpler: This component just renders the form fields, state is lifted to parent?
    // User asked for "Left part... should display the fields".
    // If I keep state here, I need to pass `formData` up on change or on save.

    // Let's pass `onChange` up? No, that's too granular.
    // Let's use an imperative handle or just let the parent control the "Save" action?
    // Simpler: The Footer is in the PARENT. So the Parent needs the data.
    // So this component should probably just be a "controlled input group".

    // REVISION: I will keep the state here and pass a `bindSave` or similar, 
    // OR just pass `formData` and `setFormData` from parent.
    // Passing state from parent is cleanest for the "Footer in Parent" requirement.
    return (
        <div className="brand-form-fields">
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
                    placeholder="e.g. Team Visma"
                />
            </div>

            <div className="form-group">
                <label>Default Color *</label>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <input
                        type="color"
                        value={formData.default_hex_color}
                        onChange={e => handleChange('default_hex_color', e.target.value)}
                        style={{ width: '40px', padding: 0, border: 'none', height: '36px', cursor: 'pointer' }}
                    />
                    <input
                        type="text"
                        value={formData.default_hex_color}
                        onChange={e => handleChange('default_hex_color', e.target.value)}
                        pattern="^#[0-9A-Fa-f]{6}$"
                        required
                        style={{ width: '100px' }}
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
                    rows={1}
                />
            </div>
        </div>
    );
}
