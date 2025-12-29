import React from 'react';
import './DiffTable.css';

/**
 * Renders a table comparing two objects.
 * Highlights differences.
 * 
 * @param {Object} props
 * @param {Object} props.before - Snapshot before change
 * @param {Object} props.after - Snapshot after change
 * @param {string} [props.className]
 */
export default function DiffTable({ before = {}, after = {}, className = '' }) {
    // Get all unique keys from both objects
    const keys = new Set([
        ...Object.keys(before || {}),
        ...Object.keys(after || {})
    ]);
    const allKeys = Array.from(keys).sort();

    if (allKeys.length === 0) {
        return <div className="diff-empty">No data to compare.</div>;
    }

    return (
        <div className={`diff-table-container ${className}`}>
            <table className="diff-table">
                <thead>
                    <tr>
                        <th className="diff-header-field">Field</th>
                        <th className="diff-header-val">Before</th>
                        <th className="diff-header-val">After</th>
                    </tr>
                </thead>
                <tbody>
                    {allKeys.map(key => {
                        const valBefore = before ? before[key] : undefined;
                        const valAfter = after ? after[key] : undefined;

                        // Determine if changed
                        // Use strict equality for primitives, JSON stringify for objects
                        const sBefore = JSON.stringify(valBefore);
                        const sAfter = JSON.stringify(valAfter);
                        const isChanged = sBefore !== sAfter;

                        return (
                            <tr key={key} className={isChanged ? 'diff-row-changed' : ''}>
                                <td className="diff-cell-field">{key}</td>
                                <td className="diff-cell-old">
                                    <DiffValue value={valBefore} />
                                </td>
                                <td className="diff-cell-new">
                                    <DiffValue value={valAfter} />
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
}

function DiffValue({ value }) {
    if (value === undefined || value === null) {
        return <span className="diff-null">-</span>;
    }

    if (typeof value === 'boolean') {
        return <code>{String(value)}</code>;
    }

    if (typeof value === 'object') {
        return <pre className="diff-json">{JSON.stringify(value, null, 2)}</pre>;
    }

    return <span className="diff-text">{String(value)}</span>;
}
