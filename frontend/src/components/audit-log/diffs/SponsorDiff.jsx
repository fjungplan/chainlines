import React from 'react';
import DiffTable from '../DiffTable';

const SPONSOR_FIELDS = [
    'legal_name',
    'display_name',
    'industry_sector'
];

const SPONSOR_LABELS = {
    legal_name: 'Legal Name',
    display_name: 'Display Name',
    industry_sector: 'Industry'
};

export default function SponsorDiff({ before, after }) {
    // Helper: Unwrap { master: params }
    const unwrap = (data) => {
        if (!data) return null;
        if (data.master && typeof data.master === 'object' && !data.legal_name) return data.master;
        return data;
    };

    const filterData = (data) => {
        const flatData = unwrap(data);
        if (!flatData) return null;
        return SPONSOR_FIELDS.reduce((acc, field) => {
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
            labels={SPONSOR_LABELS}
        />
    );
}
