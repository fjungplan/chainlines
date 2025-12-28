import React from 'react';
import './Select.css';

/**
 * Reusable Select component.
 * @param {Object} props
 * @param {string} props.label - Label text
 * @param {string} props.name - Input name/id
 * @param {Array<{value: string, label: string}>} props.options - Options array
 * @param {string|number} [props.value] - Selected value
 * @param {function} [props.onChange] - Change handler
 * @param {string} [props.error] - Error message
 * @param {boolean} [props.disabled=false] - Disabled state
 * @param {string} [props.className=''] - Additional class names
 */
export default function Select({
    label,
    name,
    options = [],
    value,
    onChange,
    error,
    disabled = false,
    className = '',
    ...props
}) {
    return (
        <div className={`input-group ${className}`}>
            {label && <label htmlFor={name}>{label}</label>}
            <select
                id={name}
                name={name}
                value={value}
                onChange={onChange}
                disabled={disabled}
                className={error ? 'error' : ''}
                {...props}
            >
                {options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                        {opt.label}
                    </option>
                ))}
            </select>
            {error && <span className="error-message">{error}</span>}
        </div>
    );
}
