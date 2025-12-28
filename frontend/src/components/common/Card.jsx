import React from 'react';
import './Card.css';

/**
 * Common Card Component
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children
 * @param {React.ReactNode} [props.title]
 * @param {React.ReactNode} [props.subtitle]
 * @param {React.ReactNode} [props.headerActions]
 * @param {string} [props.className]
 */
const Card = ({
    children,
    title,
    subtitle,
    headerActions,
    className = '',
    ...props
}) => {
    return (
        <div className={`common-card ${className}`} {...props}>
            {(title || subtitle || headerActions) && (
                <div className="card-header">
                    <div className="card-titles">
                        {title && <h3>{title}</h3>}
                        {subtitle && <div className="card-subtitle">{subtitle}</div>}
                    </div>
                    {headerActions && <div className="card-actions">{headerActions}</div>}
                </div>
            )}
            <div className="card-content">
                {children}
            </div>
        </div>
    );
};

export default Card;
