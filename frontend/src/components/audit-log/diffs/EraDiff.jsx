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
    const filterData = (data) => {
        if (!data) return null;
        return ERA_FIELDS.reduce((acc, field) => {
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
            labels={ERA_LABELS}
        />
    );
}
