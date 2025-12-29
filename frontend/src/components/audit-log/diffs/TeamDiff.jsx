import React from 'react';
import DiffTable from '../DiffTable';

const TEAM_FIELDS = [
    'legal_name',
    'display_name',
    'founding_year',
    'dissolution_year',
    'is_protected'
];

export default function TeamDiff({ before, after }) {
    const filterData = (data) => {
        if (!data) return null;
        return TEAM_FIELDS.reduce((acc, field) => {
            if (data.hasOwnProperty(field)) {
                acc[field] = data[field];
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
