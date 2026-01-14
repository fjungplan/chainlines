import React from 'react';
import DiffTable from '../DiffTable';

const LINK_FIELDS = [
    'era_name',       // Hydrated
    'brand_name',     // Hydrated
    'prominence_percent',
    'rank_order',
    'hex_color_override'
];

const LINK_LABELS = {
    era_name: 'Era Name',
    brand_name: 'Brand Name',
    prominence_percent: 'Prominence (%)',
    rank_order: 'Rank',
    hex_color_override: 'Hex Color Override'
};

export default function SponsorLinkDiff({ before, after }) {
    const unwrap = (data) => {
        if (!data) return null;
        if (data.link && typeof data.link === 'object' && !data.prominence_percent) return data.link;
        return data;
    };

    const filterData = (data) => {
        const flatData = unwrap(data);
        if (!flatData) return null;
        return LINK_FIELDS.reduce((acc, field) => {
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
            labels={LINK_LABELS}
        />
    );
}
