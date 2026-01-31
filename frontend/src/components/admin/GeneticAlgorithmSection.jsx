import React, { useEffect, useMemo } from 'react';
import SliderField from './fields/SliderField';
import NumberField from './fields/NumberField';
import ToggleField from './fields/ToggleField';
import './GeneticAlgorithmSection.css';

/**
 * GeneticAlgorithmSection - GA parameters and Mutation Strategy configuration
 * @param {Object} config - Full configuration object
 * @param {function} onChange - Callback with updated config
 * @param {function} onError - Callback for validation state (true if error)
 */
export default function GeneticAlgorithmSection({ config, onChange, onError }) {
    const gaConfig = config.GENETIC_ALGORITHM;
    const strategies = config.MUTATION_STRATEGIES || {
        SWAP: 0.2,
        HEURISTIC: 0.2,
        COMPACTION: 0.3,
        EXPLORATION: 0.3
    };
    const scoreboard = config.SCOREBOARD;

    // Calculate sum of mutation strategies
    const totalProbability = useMemo(() => {
        const sum = Object.values(strategies).reduce((acc, val) => acc + val, 0);
        return parseFloat(sum.toFixed(2));
    }, [strategies]);

    const isValid = Math.abs(totalProbability - 1.0) < 0.01;

    // Notify parent of error state
    useEffect(() => {
        if (onError) {
            onError(!isValid);
        }
    }, [isValid, onError]);

    const handleGaChange = (field, value) => {
        onChange({
            ...config,
            GENETIC_ALGORITHM: {
                ...gaConfig,
                [field]: value
            }
        });
    };

    const handleStrategyChange = (field, value) => {
        onChange({
            ...config,
            MUTATION_STRATEGIES: {
                ...strategies,
                [field]: value
            }
        });
    };

    const handleScoreboardChange = (value) => {
        onChange({
            ...config,
            SCOREBOARD: {
                ...scoreboard,
                ENABLED: value
            }
        });
    };

    return (
        <div className="settings-section ga-section">
            <h2>Genetic Algorithm</h2>

            <div className="scoreboard-toggle-wrapper">
                <ToggleField
                    label="Enable Scoreboard"
                    checked={scoreboard.ENABLED}
                    onChange={handleScoreboardChange}
                    tooltip="Display live scoreboard during optimization (saves scores to disk)"
                />
            </div>

            <div className="settings-subsection">
                <h3>Population Parameters</h3>
                <div className="grid-2 no-divider">
                    <NumberField
                        label="Population Size"
                        value={gaConfig.POP_SIZE}
                        onChange={(val) => handleGaChange('POP_SIZE', val)}
                        min={10}
                        max={10000}
                        step={10}
                        tooltip="Number of individuals in each generation (typical: 1000)"
                    />
                    <NumberField
                        label="Generations"
                        value={gaConfig.GENERATIONS}
                        onChange={(val) => handleGaChange('GENERATIONS', val)}
                        min={100}
                        max={50000}
                        step={100}
                        tooltip="Max generations to run (typical: 5000)"
                    />
                </div>
                <div className="grid-2">
                    <SliderField
                        label="Mutation Rate"
                        value={gaConfig.MUTATION_RATE}
                        onChange={(val) => handleGaChange('MUTATION_RATE', val)}
                        min={0}
                        max={1}
                        step={0.01}
                        tooltip="Probability of mutation per individual (typical: 0.2)"
                    />
                    <SliderField
                        label="Tournament Size"
                        value={gaConfig.TOURNAMENT_SIZE}
                        onChange={(val) => handleGaChange('TOURNAMENT_SIZE', val)}
                        min={2}
                        max={50}
                        step={1}
                        decimals={0}
                        tooltip="Size of tournament for selection (typical: 10)"
                    />
                </div>
                <div className="grid-2">
                    <NumberField
                        label="Timeout (seconds)"
                        value={gaConfig.TIMEOUT_SECONDS}
                        onChange={(val) => handleGaChange('TIMEOUT_SECONDS', val)}
                        min={10}
                        max={36000}
                        step={10}
                        tooltip="Maximum time to run optimization before forced exit"
                    />
                    <NumberField
                        label="Patience (generations)"
                        value={gaConfig.PATIENCE}
                        onChange={(val) => handleGaChange('PATIENCE', val)}
                        min={10}
                        max={5000}
                        step={10}
                        tooltip="Stop if no improvement for this many generations"
                    />
                </div>
            </div>

            <div className="settings-subsection mutation-group">
                <h3>Mutation Strategies</h3>
                <div className={`validation-status ${isValid ? 'valid' : 'invalid'}`} data-testid="validation-status">
                    <span>Total Probability: {totalProbability.toFixed(2)}</span>
                    {!isValid && <span className="error-msg"> (Must sum to 1.0)</span>}
                </div>

                <div className="grid-2">
                    <SliderField
                        label="Swap Probability"
                        value={strategies.SWAP}
                        onChange={(val) => handleStrategyChange('SWAP', val)}
                        min={0}
                        max={1}
                        step={0.05}
                        tooltip="Probability of swapping two nodes"
                    />
                    <SliderField
                        label="Heuristic Probability"
                        value={strategies.HEURISTIC}
                        onChange={(val) => handleStrategyChange('HEURISTIC', val)}
                        min={0}
                        max={1}
                        step={0.05}
                        tooltip="Probability of heuristic improvement"
                    />
                    <SliderField
                        label="Compaction Probability"
                        value={strategies.COMPACTION}
                        onChange={(val) => handleStrategyChange('COMPACTION', val)}
                        min={0}
                        max={1}
                        step={0.05}
                        tooltip="Probability of compacting layout"
                    />
                    <SliderField
                        label="Exploration Probability"
                        value={strategies.EXPLORATION}
                        onChange={(val) => handleStrategyChange('EXPLORATION', val)}
                        min={0}
                        max={1}
                        step={0.05}
                        tooltip="Probability of varying layout randomly"
                    />
                </div>
            </div>
        </div>
    );
}
