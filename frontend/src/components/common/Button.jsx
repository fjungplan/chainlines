import React from 'react';
import './Button.css';

/**
 * Common Button Component
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children
 * @param {'default'|'primary'|'secondary'|'danger'|'success'|'outline'|'ghost'|'icon'} [props.variant='default']
 * @param {'md'|'sm'|'lg'} [props.size='md']
 * @param {boolean} [props.active=false]
 * @param {'button'|'submit'|'reset'} [props.type='button']
 * @param {boolean} [props.disabled=false]
 * @param {string} [props.className='']
 * @param {function} [props.onClick]
 */
const Button = ({
    children,
    variant = 'default',
    size = 'md',
    active = false,
    type = 'button',
    disabled = false,
    className = '',
    onClick,
    ...props
}) => {
    // Base class 'btn' is global from index.css (to be moved)
    let btnClass = 'btn';

    if (variant && variant !== 'default') {
        btnClass += ` btn-${variant}`;
    }

    if (size && size !== 'md') {
        btnClass += ` btn-${size}`;
    }

    if (active) {
        btnClass += ' active';
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
