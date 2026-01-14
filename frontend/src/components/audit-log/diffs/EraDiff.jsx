import React from 'react';
import DiffTable from '../DiffTable';

const ERA_FIELDS = [
    'registered_name',
    'uci_code',
    'country_code',
    'tier_level',
    'valid_from',
    'season_year'
];

const ERA_LABELS = {
    registered_name: 'Registered Name',
    uci_code: 'UCI Code',
    country_code: 'Country',
    tier_level: 'Tier',
    valid_from: 'Valid From',
    season_year: 'Season'
};

export default function EraDiff({ before, after }) {
    // Helper to unwrap nested data (e.g. from scraper: { era: { ... } })
    const unwrap = (data) => {
        if (!data) return null;
        if (data.era && typeof data.era === 'object' && !data.registered_name) {
            return data.era;
        }
        return data;
    };

    const filterData = (data) => {
        const flatData = unwrap(data);
        if (!flatData) return null;

        return ERA_FIELDS.reduce((acc, field) => {
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
            labels={ERA_LABELS}
        />
    );
}
