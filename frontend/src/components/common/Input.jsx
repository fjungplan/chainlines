import React from 'react';
import './Input.css';

/**
 * Reusable Input component.
 * @param {Object} props
 * @param {string} props.label - Label text
 * @param {string} props.name - Input name/id
 * @param {string} [props.type='text'] - Input type
 * @param {string|number} [props.value] - Input value
 * @param {function} [props.onChange] - Change handler
 * @param {string} [props.error] - Error message
 * @param {boolean} [props.disabled=false] - Disabled state
 * @param {string} [props.className=''] - Additional class names
 */
export default function Input({
    label,
    name,
    type = 'text',
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
            {type === 'textarea' ? (
                <textarea
                    id={name}
                    name={name}
                    value={value}
                    onChange={onChange}
                    disabled={disabled}
                    className={error ? 'error' : ''}
                    {...props}
                />
            ) : (
                <input
                    id={name}
                    name={name}
                    type={type}
                    value={value}
                    onChange={onChange}
                    disabled={disabled}
                    className={error ? 'error' : ''}
                    {...props}
                />
            )}
            {error && <span className="error-message">{error}</span>}
        </div>
    );
}
