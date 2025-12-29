import React from 'react';
import DiffTable from '../DiffTable';

const LINEAGE_FIELDS = [
    'lineage_type',
    'year',
    'predecessor_names',
    'successor_names',
    'team_name' // Sometimes relevant for rebrand
];

export default function LineageDiff({ before, after }) {
    const filterData = (data) => {
        if (!data) return null;
        return LINEAGE_FIELDS.reduce((acc, field) => {
            if (data.hasOwnProperty(field)) {
                // Formatting for list fields to be strings so DiffTable compares them nicely
                if (Array.isArray(data[field])) {
                    acc[field] = data[field].join(', ');
                } else {
                    acc[field] = data[field];
                }
            }
            return acc;
        }, {});
    };

    return (
        <DiffTable
            before={filterData(before)}
            after={filterData(after)}
        />
    );
}
