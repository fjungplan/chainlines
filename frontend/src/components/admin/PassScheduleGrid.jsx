import React from 'react';
import './PassScheduleGrid.css';

/**
 * PassScheduleGrid - Dynamic grid for configuring optimization passes
 * @param {Array} schedule - Array of pass configurations
 * @param {function} onChange - Callback with updated schedule
 */
export default function PassScheduleGrid({ schedule, onChange }) {
    const STRATEGY_OPTIONS = ['PARENTS', 'CHILDREN', 'HUBS', 'HYBRID'];

    const handleAddRow = () => {
        onChange([
            ...schedule,
            {
                strategies: [],
                iterations: 100,
                min_family_size: 3,
                min_links: 2
            }
        ]);
    };

    const handleRemoveRow = (index) => {
        const newSchedule = schedule.filter((_, i) => i !== index);
        onChange(newSchedule);
    };

    const handleStrategyToggle = (rowIndex, strategy) => {
        const newSchedule = [...schedule];
        const currentStrategies = newSchedule[rowIndex].strategies;

        // Check if strategy is already selected
        const isSelected = currentStrategies.includes(strategy);

        if (isSelected) {
            // Remove strategy
            newSchedule[rowIndex].strategies = currentStrategies.filter(s => s !== strategy);
        } else {
            // Add strategy with exclusivity logic
            if (strategy === 'HYBRID') {
                // HYBRID is exclusive - clear all others
                newSchedule[rowIndex].strategies = ['HYBRID'];
            } else {
                // Adding non-HYBRID strategy - remove HYBRID if present
                const withoutHybrid = currentStrategies.filter(s => s !== 'HYBRID');
                newSchedule[rowIndex].strategies = [...withoutHybrid, strategy];
            }
        }

        onChange(newSchedule);
    };

    const handleFieldChange = (rowIndex, field, value) => {
        const newSchedule = [...schedule];
        newSchedule[rowIndex][field] = parseInt(value) || 0;
        onChange(newSchedule);
    };

    const isStrategyDisabled = (rowStrategies, strategy) => {
        if (strategy === 'HYBRID') {
            // HYBRID is disabled if any other strategy is selected
            return rowStrategies.some(s => s !== 'HYBRID');
        } else {
            // Other strategies are disabled if HYBRID is selected
            return rowStrategies.includes('HYBRID');
        }
    };

    return (
        <div className="pass-schedule-grid">
            <table>
                <thead>
                    <tr>
                        <th>Strategies</th>
                        <th>Iterations</th>
                        <th>Min Family</th>
                        <th>Min Links</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {schedule.map((pass, index) => (
                        <tr key={index}>
                            <td>
                                <div className="strategy-selector">
                                    {STRATEGY_OPTIONS.map(strategy => {
                                        const isSelected = pass.strategies.includes(strategy);
                                        const isDisabled = !isSelected && isStrategyDisabled(pass.strategies, strategy);

                                        return (
                                            <label
                                                key={strategy}
                                                className={`strategy-option ${isDisabled ? 'disabled' : ''}`}
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={isSelected}
                                                    disabled={isDisabled}
                                                    onChange={() => handleStrategyToggle(index, strategy)}
                                                />
                                                <span>{strategy}</span>
                                            </label>
                                        );
                                    })}
                                </div>
                            </td>
                            <td>
                                <input
                                    type="number"
                                    value={pass.iterations}
                                    onChange={(e) => handleFieldChange(index, 'iterations', e.target.value)}
                                    min={1}
                                    max={10000}
                                />
                            </td>
                            <td>
                                <input
                                    type="number"
                                    value={pass.min_family_size}
                                    onChange={(e) => handleFieldChange(index, 'min_family_size', e.target.value)}
                                    min={1}
                                    max={100}
                                />
                            </td>
                            <td>
                                <input
                                    type="number"
                                    value={pass.min_links}
                                    onChange={(e) => handleFieldChange(index, 'min_links', e.target.value)}
                                    min={1}
                                    max={100}
                                />
                            </td>
                            <td>
                                <button
                                    className="btn btn-sm btn-danger"
                                    onClick={() => handleRemoveRow(index)}
                                    disabled={schedule.length === 1}
                                    title="Remove this pass"
                                >
                                    Remove
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            <button
                className="btn btn-primary btn-sm"
                onClick={handleAddRow}
            >
                + Add Pass
            </button>
        </div>
    );
}
