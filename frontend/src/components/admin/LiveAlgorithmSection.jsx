import React from 'react';
import NumberField from './fields/NumberField';
import ToggleField from './fields/ToggleField';
import PassScheduleGrid from './PassScheduleGrid';
import './LiveAlgorithmSection.css';

/**
 * LiveAlgorithmSection - Groupwise parameters and Pass Schedule configuration
 * @param {Object} config - Configuration object with GROUPWISE and PASS_SCHEDULE
 * @param {function} onChange - Callback with updated config
 */
export default function LiveAlgorithmSection({ config, onChange }) {
    const handleGroupwiseChange = (field, value) => {
        onChange({
            ...config,
            GROUPWISE: {
                ...config.GROUPWISE,
                [field]: value
            }
        });
    };

    const handleScheduleChange = (newSchedule) => {
        onChange({
            ...config,
            PASS_SCHEDULE: newSchedule
        });
    };

    return (
        <div className="live-algorithm-section">
            <h2>Live Algorithm</h2>

            <div className="section-group">
                <h3>Groupwise Parameters</h3>
                <div className="field-grid">
                    <NumberField
                        label="Min Family Size"
                        value={config.GROUPWISE.MIN_FAMILY_SIZE}
                        onChange={(val) => handleGroupwiseChange('MIN_FAMILY_SIZE', val)}
                        min={1}
                        max={100}
                        tooltip="Minimum number of teams in a family to apply groupwise optimization"
                    />
                    <NumberField
                        label="Min Links"
                        value={config.GROUPWISE.MIN_LINKS}
                        onChange={(val) => handleGroupwiseChange('MIN_LINKS', val)}
                        min={1}
                        max={100}
                        tooltip="Minimum number of links required for groupwise optimization"
                    />
                </div>

                <ToggleField
                    label="Enable Scoreboard"
                    checked={config.GROUPWISE.ENABLE_SCOREBOARD}
                    onChange={(val) => handleGroupwiseChange('ENABLE_SCOREBOARD', val)}
                    tooltip="Display live scoreboard during optimization"
                />
            </div>

            <div className="section-group">
                <h3>Pass Schedule</h3>
                <PassScheduleGrid
                    schedule={config.PASS_SCHEDULE}
                    onChange={handleScheduleChange}
                />
            </div>
        </div>
    );
}
