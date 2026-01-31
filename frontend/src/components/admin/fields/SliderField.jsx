import React from 'react';
import InfoTooltip from './InfoTooltip';
import './Fields.css';

/**
 * SliderField component with value display
 * @param {string} label - Field label
 * @param {number} value - Current value
 * @param {function} onChange - Change handler (receives number)
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @param {number} [step=0.01] - Step increment
 * @param {string} [tooltip] - Tooltip content
 * @param {number} [decimals=2] - Number of decimals to display
 */
export default function SliderField({
    label,
    value,
    onChange,
    min,
    max,
    step = 0.01,
    tooltip,
    decimals = 2,
    ...props
}) {
    const handleChange = (e) => {
        const newValue = parseFloat(e.target.value);
        onChange(newValue);
    };

    // Generate unique ID from label
    const fieldId = `slider-${label.toLowerCase().replace(/\s+/g, '-')}`;

    return (
        <div className="field-group slider-field">
            <label htmlFor={fieldId}>
                {label}
                {tooltip && <InfoTooltip content={tooltip} />}
            </label>
            <div className="slider-container">
                <input
                    id={fieldId}
                    type="range"
                    value={value}
                    onChange={handleChange}
                    min={min}
                    max={max}
                    step={step}
                    {...props}
                />
                <span className="slider-value">{value.toFixed(decimals)}</span>
            </div>
        </div>
    );
}
