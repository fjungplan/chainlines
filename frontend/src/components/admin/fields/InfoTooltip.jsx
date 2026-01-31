import React, { useState } from 'react';
import './Fields.css';

/**
 * InfoTooltip component - displays info icon with hover tooltip
 * @param {string} content - Tooltip content
 */
export default function InfoTooltip({ content }) {
    const [visible, setVisible] = useState(false);

    return (
        <span
            className="info-tooltip"
            onMouseEnter={() => setVisible(true)}
            onMouseLeave={() => setVisible(false)}
            title={content}
        >
            ⓘ
            {visible && (
                <span className="tooltip-content">
                    {content}
                </span>
            )}
        </span>
    );
}
