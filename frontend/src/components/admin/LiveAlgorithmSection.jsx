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
        <div className="settings-section live-algorithm-section">
            <h2>Live Algorithm</h2>

            <div className="settings-subsection">
                <h3>Groupwise Parameters (Simulated Annealing)</h3>
                <div className="grid-4">
                    <NumberField
                        label="Max Rigid Delta"
                        value={config.GROUPWISE.MAX_RIGID_DELTA}
                        onChange={(val) => handleGroupwiseChange('MAX_RIGID_DELTA', val)}
                        min={1}
                        max={100}
                        tooltip="Maximum allowed movement for rigid group moves"
                    />
                    <NumberField
                        label="SA Max Iterations"
                        value={config.GROUPWISE.SA_MAX_ITER}
                        onChange={(val) => handleGroupwiseChange('SA_MAX_ITER', val)}
                        min={1}
                        max={1000}
                        tooltip="Maximum iterations for Simulated Annealing"
                    />
                    <NumberField
                        label="SA Initial Temp"
                        value={config.GROUPWISE.SA_INITIAL_TEMP}
                        onChange={(val) => handleGroupwiseChange('SA_INITIAL_TEMP', val)}
                        min={1}
                        max={1000}
                        tooltip="Initial temperature for Simulated Annealing"
                    />
                    <NumberField
                        label="Search Radius"
                        value={config.GROUPWISE.SEARCH_RADIUS}
                        onChange={(val) => handleGroupwiseChange('SEARCH_RADIUS', val)}
                        min={1}
                        max={100}
                        tooltip="Radius for local search in groupwise optimization"
                    />
                </div>
            </div>

            <div className="settings-subsection">
                <h3>Pass Schedule</h3>
                <PassScheduleGrid
                    schedule={config.PASS_SCHEDULE}
                    onChange={handleScheduleChange}
                />
            </div>
        </div>
    );
}
