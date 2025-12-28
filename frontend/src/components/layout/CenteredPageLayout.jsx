import React from 'react';
import './CenteredPageLayout.css';

/**
 * Centered Page Layout
 * Provides a centered container for standard pages like About, Login, etc.
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children
 * @param {string} [props.className]
 */
const CenteredPageLayout = ({ children, className = '' }) => {
    return (
        <div className={`centered-page-layout ${className}`}>
            {children}
        </div>
    );
};

export default CenteredPageLayout;
