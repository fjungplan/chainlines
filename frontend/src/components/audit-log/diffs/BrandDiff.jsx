import React from 'react';
import DiffTable from '../DiffTable';

const BRAND_FIELDS = [
    'brand_name',
    'display_name',
    'default_hex_color'
];

const BRAND_LABELS = {
    brand_name: 'Brand Name',
    display_name: 'Display Name',
    default_hex_color: 'Brand Color'
};

export default function BrandDiff({ before, after }) {
    const unwrap = (data) => {
        if (!data) return null;
        if (data.brand && typeof data.brand === 'object' && !data.brand_name) return data.brand;
        return data;
    };

    const filterData = (data) => {
        const flatData = unwrap(data);
        if (!flatData) return null;
        return BRAND_FIELDS.reduce((acc, field) => {
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
            labels={BRAND_LABELS}
        />
    );
}
