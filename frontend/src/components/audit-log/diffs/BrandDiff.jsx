import React from 'react';
import DiffTable from '../DiffTable';

const BRAND_FIELDS = [
    'brand_name',
    'display_name',
    'default_hex_color'
];

export default function BrandDiff({ before, after }) {
    const filterData = (data) => {
        if (!data) return null;
        return BRAND_FIELDS.reduce((acc, field) => {
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
