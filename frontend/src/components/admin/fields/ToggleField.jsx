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

    return (
        <div className="field-group toggle-field">
            <label>
                {label}
                {tooltip && <InfoTooltip content={tooltip} />}
            </label>
            <input
                type="checkbox"
                checked={value}
                onChange={handleChange}
                {...props}
            />
        </div>
    );
}
