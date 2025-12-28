/**
 * Date formatting utilities using browser/system locale settings.
 * All date/time display should use these functions for consistency.
 */

/**
 * Format a date string or Date object using the user's locale.
 * Shows only the date (no time).
 * 
 * @param {string|Date|null|undefined} dateInput - The date to format
 * @param {string} fallback - Fallback string if date is null/undefined
 * @returns {string} Formatted date string
 */
export function formatDate(dateInput, fallback = '-') {
    if (!dateInput) return fallback;

    try {
        const date = new Date(dateInput);
        if (isNaN(date.getTime())) return fallback;

        return date.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch {
        return fallback;
    }
}

/**
 * Format a date string or Date object using the user's locale.
 * Shows both date and time.
 * 
 * @param {string|Date|null|undefined} dateInput - The date to format
 * @param {string} fallback - Fallback string if date is null/undefined
 * @returns {string} Formatted datetime string
 */
export function formatDateTime(dateInput, fallback = '-') {
    if (!dateInput) return fallback;

    try {
        const date = new Date(dateInput);
        if (isNaN(date.getTime())) return fallback;

        return date.toLocaleString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return fallback;
    }
}

/**
 * Format a date for display in a compact form (useful for tables).
 * 
 * @param {string|Date|null|undefined} dateInput - The date to format
 * @param {string} fallback - Fallback string if date is null/undefined
 * @returns {string} Formatted date string
 */
export function formatDateCompact(dateInput, fallback = '-') {
    if (!dateInput) return fallback;

    try {
        const date = new Date(dateInput);
        if (isNaN(date.getTime())) return fallback;

        return date.toLocaleDateString(undefined, {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    } catch {
        return fallback;
    }
}

/**
 * Format a relative time (e.g., "2 hours ago", "3 days ago").
 * Falls back to formatted date if too old.
 * 
 * @param {string|Date|null|undefined} dateInput - The date to format
 * @param {string} fallback - Fallback string if date is null/undefined
 * @returns {string} Relative time string
 */
export function formatRelativeTime(dateInput, fallback = '-') {
    if (!dateInput) return fallback;

    try {
        const date = new Date(dateInput);
        if (isNaN(date.getTime())) return fallback;

        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} min ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        // Fall back to date format for older dates
        return formatDate(date, fallback);
    } catch {
        return fallback;
    }
}
