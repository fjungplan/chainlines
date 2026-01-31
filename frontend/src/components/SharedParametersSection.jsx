import React from 'react';
import SliderField from './admin/fields/SliderField';
import './SharedParametersSection.css';

/**
 * SharedParametersSection - Global weights and geometric parameters
 * @param {Object} config - Full configuration object
 * @param {function} onChange - Callback with updated config
 */
export default function SharedParametersSection({ config, onChange }) {
    const handleRadiusChange = (field, value) => {
        onChange({
            ...config,
            [field]: value
        });
    };

    const handleWeightChange = (field, value) => {
        onChange({
            ...config,
            WEIGHTS: {
                ...config.WEIGHTS,
                [field]: value
            }
        });
    };

    return (
        <div className="settings-section shared-parameters-section">
            <h2>Shared Parameters</h2>

            <div className="settings-subsection">
                <h3>Geometric Parameters</h3>
                <div className="grid-2">
                    <SliderField
                        label="Search Radius"
                        value={config.SEARCH_RADIUS}
                        onChange={(val) => handleRadiusChange('SEARCH_RADIUS', val)}
                        min={10}
                        max={100}
                        step={1}
                        decimals={0}
                        tooltip="Radius for neighbor search (typical: 50)"
                    />
                    <SliderField
                        label="Target Radius"
                        value={config.TARGET_RADIUS}
                        onChange={(val) => handleRadiusChange('TARGET_RADIUS', val)}
                        min={5}
                        max={50}
                        step={1}
                        decimals={0}
                        tooltip="Target radius for positioning (typical: 10)"
                    />
                </div>
            </div>

            <div className="settings-subsection">
                <h3>Cost Weights</h3>
                <div className="grid-2">
                    <SliderField
                        label="Attraction"
                        value={config.WEIGHTS.ATTRACTION}
                        onChange={(val) => handleWeightChange('ATTRACTION', val)}
                        min={0}
                        max={5000}
                        step={100}
                        decimals={0}
                        tooltip="Weight for parent-child attraction (typical: 1000)"
                    />
                    <SliderField
                        label="Y Shape"
                        value={config.WEIGHTS.Y_SHAPE}
                        onChange={(val) => handleWeightChange('Y_SHAPE', val)}
                        min={0}
                        max={2000}
                        step={50}
                        decimals={0}
                        tooltip="Penalty for Y-shaped patterns (typical: 500)"
                    />
                    <SliderField
                        label="Cut Through"
                        value={config.WEIGHTS.CUT_THROUGH}
                        onChange={(val) => handleWeightChange('CUT_THROUGH', val)}
                        min={0}
                        max={20000}
                        step={500}
                        decimals={0}
                        tooltip="Penalty for cutting through relationships (typical: 10000)"
                    />
                    <SliderField
                        label="Blocker"
                        value={config.WEIGHTS.BLOCKER}
                        onChange={(val) => handleWeightChange('BLOCKER', val)}
                        min={0}
                        max={10000}
                        step={250}
                        decimals={0}
                        tooltip="Penalty for blocker relationships (typical: 5000)"
                    />
                    <SliderField
                        label="Overlap Base"
                        value={config.WEIGHTS.OVERLAP_BASE}
                        onChange={(val) => handleWeightChange('OVERLAP_BASE', val)}
                        min={0}
                        max={1000000}
                        step={10000}
                        decimals={0}
                        tooltip="Base penalty for overlaps (typical: 500000)"
                    />
                    <SliderField
                        label="Overlap Factor"
                        value={config.WEIGHTS.OVERLAP_FACTOR}
                        onChange={(val) => handleWeightChange('OVERLAP_FACTOR', val)}
                        min={0}
                        max={50000}
                        step={1000}
                        decimals={0}
                        tooltip="Multiplier for overlap severity (typical: 10000)"
                    />
                    <SliderField
                        label="Lane Sharing"
                        value={config.WEIGHTS.LANE_SHARING}
                        onChange={(val) => handleWeightChange('LANE_SHARING', val)}
                        min={0}
                        max={5000}
                        step={100}
                        decimals={0}
                        tooltip="Penalty for lane sharing (typical: 1000)"
                    />
                </div>
            </div>
        </div>
    );
}
