import React from 'react';
import InfoTooltip from './InfoTooltip';
import './Fields.css';

/**
 * NumberField component for integer/float inputs
 * @param {string} label - Field label
 * @param {number} value - Current value
 * @param {function} onChange - Change handler (receives number)
 * @param {number} [min] - Minimum value
 * @param {number} [max] - Maximum value
 * @param {number} [step=1] - Step increment
 * @param {string} [tooltip] - Tooltip content
 */
export default function NumberField({
    label,
    value,
    onChange,
    min,
    max,
    step = 1,
    tooltip,
    ...props
}) {
    const handleChange = (e) => {
        const newValue = parseFloat(e.target.value);
        if (!isNaN(newValue)) {
            onChange(newValue);
        }
    };

    // Generate unique ID from label
    const fieldId = `number-${label.toLowerCase().replace(/\s+/g, '-')}`;

    return (
        <div className="field-group">
            <label htmlFor={fieldId}>
                {label}
                {tooltip && <InfoTooltip content={tooltip} />}
            </label>
            <input
                id={fieldId}
                type="number"
                value={value}
                onChange={handleChange}
                min={min}
                max={max}
                step={step}
                {...props}
            />
        </div>
    );
}
