import React from 'react';
import DiffTable from '../DiffTable';

const TEAM_FIELDS = [
    'legal_name',
    'display_name',
    'founding_year',
    'dissolution_year',
    'is_protected',
    'registered_name', // Handle potential Era vs Node key mismatch
    'season_year'
];

const TEAM_LABELS = {
    legal_name: 'Legal Name',
    display_name: 'Display Name',
    founding_year: 'Founding Year',
    dissolution_year: 'Dissolution Year',
    is_protected: 'Protected',
    registered_name: 'Registered Name',
    season_year: 'Season Year'
};


export default function TeamDiff({ before, after }) {
    // Helper to unwrap nested data (e.g. from scraper: { node: { ... } })
    const unwrap = (data) => {
        if (!data) return null;
        if (data.node && typeof data.node === 'object' && !data.legal_name) {
            return data.node;
        }
        return data;
    };

    const filterData = (data) => {
        const flatData = unwrap(data);
        if (!flatData) return null;

        return TEAM_FIELDS.reduce((acc, field) => {
            if (flatData.hasOwnProperty(field)) {
                acc[field] = flatData[field];
            }
            return acc;
        }, {});
    };

    return (
        <DiffTable
            before={filterData(before)}
            after={filterData(after)}
            labels={TEAM_LABELS}
        />
    );
}
