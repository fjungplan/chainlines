import React from 'react';
import './NotificationBadge.css';

/**
 * A notification badge that displays a count.
 * Hidden if count is 0, null, or undefined.
 * 
 * @param {Object} props
 * @param {number} props.count - The number to display
 */
export default function NotificationBadge({ count }) {
    if (!count || count <= 0) return null;

    return (
        <span className="notification-badge">
            {count}
        </span>
    );
}
