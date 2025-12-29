import React from 'react';
import DiffTable from '../DiffTable';

const SPONSOR_FIELDS = [
    'legal_name',
    'display_name',
    'industry_sector'
];

export default function SponsorDiff({ before, after }) {
    const filterData = (data) => {
        if (!data) return null;
        return SPONSOR_FIELDS.reduce((acc, field) => {
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
