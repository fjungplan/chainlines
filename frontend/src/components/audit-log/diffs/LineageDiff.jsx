import React from 'react';
import DiffTable from '../DiffTable';

const LINEAGE_FIELDS = [
    'event_type',        // Scraper uses this
    'lineage_type',      // Legacy/API
    'event_year',        // Scraper uses this
    'year',              // Legacy/API
    'source_node',       // Scraper Name
    'target_team',       // Scraper Name
    'predecessor_names', // Legacy/API
    'successor_names',   // Legacy/API
    'predecessor_node_id', // Scraper ID
    'successor_node_id',   // Scraper ID
    'reasoning',         // Context
    'confidence'         // Context
];

const LINEAGE_LABELS = {
    event_type: "Type",
    lineage_type: "Type",
    event_year: "Year",
    year: "Year",
    source_node: "Predecessor (Name)",
    target_team: "Successor (Name)",
    predecessor_names: "Predecessor",
    successor_names: "Successor",
    predecessor_node_id: "Predecessor ID",
    successor_node_id: "Successor ID",
    reasoning: "Reasoning",
    confidence: "Confidence"
};

export default function LineageDiff({ before, after }) {
    const unwrap = (data) => {
        if (!data) return null;
        // Check for 'event' (common) or 'lineage_event' wrapper
        if (data.event && typeof data.event === 'object' && !data.event_type) return data.event;
        if (data.lineage_event && typeof data.lineage_event === 'object' && !data.event_type) return data.lineage_event;
        return data;
    };

    const filterData = (data) => {
        const flatData = unwrap(data);
        if (!flatData) return null;

        const result = {};

        // Helper to check if we have a name value
        const hasName = (nameField) => flatData.hasOwnProperty(nameField) && flatData[nameField];

        LINEAGE_FIELDS.forEach(field => {
            if (flatData.hasOwnProperty(field)) {
                // Skip ID fields if we have the corresponding Name field
                if (field === 'predecessor_node_id' && (hasName('source_node') || hasName('predecessor_names'))) return;
                if (field === 'successor_node_id' && (hasName('target_team') || hasName('successor_names'))) return;

                // Formatting for list fields to be strings so DiffTable compares them nicely
                if (Array.isArray(flatData[field])) {
                    result[field] = flatData[field].join(', ');
                } else {
                    result[field] = flatData[field];
                }
            }
        });

        return result;
    };

    return (
        <DiffTable
            before={filterData(before)}
            after={filterData(after)}
            labels={LINEAGE_LABELS}
        />
    );
}
