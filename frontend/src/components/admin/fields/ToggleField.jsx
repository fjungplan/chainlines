import React from 'react';
import InfoTooltip from './InfoTooltip';
import './Fields.css';

/**
 * ToggleField component (checkbox styled as toggle switch)
 * @param {string} label - Field label
 * @param {boolean} value - Current value
 * @param {function} onChange - Change handler (receives boolean)
 * @param {string} [tooltip] - Tooltip content
 */
export default function ToggleField({
    label,
    value,
    onChange,
    tooltip,
    ...props
}) {
    const handleChange = (e) => {
        onChange(e.target.checked);
    };

    // Generate unique ID from label
    const fieldId = `toggle-${label.toLowerCase().replace(/\s+/g, '-')}`;

    return (
        <div className="field-group toggle-field">
            <label htmlFor={fieldId}>
                {label}
                {tooltip && <InfoTooltip content={tooltip} />}
            </label>
            <input
                id={fieldId}
                type="checkbox"
                checked={value}
                onChange={handleChange}
                {...props}
            />
        </div>
    );
}
