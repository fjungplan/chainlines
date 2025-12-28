import React from 'react';
import './Button.css';

/**
 * Common Button Component
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children
 * @param {'default'|'primary'|'secondary'|'danger'|'success'|'sm'|'small'} [props.variant='default']
 * @param {'button'|'submit'|'reset'} [props.type='button']
 * @param {boolean} [props.disabled=false]
 * @param {string} [props.className='']
 * @param {function} [props.onClick]
 */
const Button = ({
    children,
    variant = 'default',
    type = 'button',
    disabled = false,
    className = '',
    onClick,
    ...props
}) => {
    // Base class 'btn' is global from index.css
    let btnClass = 'btn';

    if (variant && variant !== 'default') {
        btnClass += ` btn-${variant}`;
    }

    if (className) {
        btnClass += ` ${className}`;
    }

    return (
        <button
            type={type}
            className={btnClass}
            onClick={onClick}
            disabled={disabled}
            {...props}
        >
            {children}
        </button>
    );
};

export default Button;
