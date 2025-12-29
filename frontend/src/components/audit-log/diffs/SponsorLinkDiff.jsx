import React from 'react';
import DiffTable from '../DiffTable';

const LINK_FIELDS = [
    'era_name',
    'brand_name',
    'prominence',
    'rank',
    'hex_color_override'
];

export default function SponsorLinkDiff({ before, after }) {
    const filterData = (data) => {
        if (!data) return null;
        return LINK_FIELDS.reduce((acc, field) => {
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
