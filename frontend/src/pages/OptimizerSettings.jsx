import React, { useState, useEffect } from 'react';
import LiveAlgorithmSection from '../components/admin/LiveAlgorithmSection';
import SharedParametersSection from '../components/SharedParametersSection';
import GeneticAlgorithmSection from '../components/admin/GeneticAlgorithmSection';
import { optimizerConfigApi } from '../api/optimizerConfig';
import './OptimizerSettings.css';

export default function OptimizerSettings() {
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [hasValidationError, setHasValidationError] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await optimizerConfigApi.getConfig();
            setConfig(data);
        } catch (err) {
            setError('Failed to load configuration: ' + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (hasValidationError) {
            setError('Cannot save: Mutation strategies must sum to 1.0');
            return;
        }

        try {
            setSaving(true);
            setError(null);
            setSuccessMessage('');
            await optimizerConfigApi.updateConfig(config);
            setSuccessMessage('Configuration saved successfully!');
            setTimeout(() => setSuccessMessage(''), 3000);
        } catch (err) {
            setError('Failed to save configuration: ' + (err.response?.data?.detail || err.message));
        } finally {
            setSaving(false);
        }
    };

    const handleLiveChange = (updatedLiveConfig) => {
        setConfig({
            ...config,
            GROUPWISE: updatedLiveConfig.GROUPWISE,
            PASS_SCHEDULE: updatedLiveConfig.PASS_SCHEDULE
        });
    };

    const handleSharedChange = (updatedSharedConfig) => {
        setConfig({
            ...config,
            SEARCH_RADIUS: updatedSharedConfig.SEARCH_RADIUS,
            TARGET_RADIUS: updatedSharedConfig.TARGET_RADIUS,
            SCORES: updatedSharedConfig.SCORES
        });
    };

    const handleGAChange = (updatedGAConfig) => {
        setConfig({
            ...config,
            GENETIC_ALGORITHM: updatedGAConfig.GENETIC_ALGORITHM,
            MUTATION_STRATEGIES: updatedGAConfig.MUTATION_STRATEGIES
        });
    };

    if (loading) {
        return (
            <div className="centered-page-container">
                <div className="centered-content-card">
                    <div className="loading-spinner">Loading configuration...</div>
                </div>
            </div>
        );
    }

    if (!config) {
        return (
            <div className="centered-page-container">
                <div className="centered-content-card">
                    <div className="error-message">{error || 'Failed to load configuration'}</div>
                </div>
            </div>
        );
    }

    return (
        <div className="centered-page-container">
            <div className="optimizer-settings-container">
                <div className="settings-header">
                    <a href="/admin/optimizer" className="back-link">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                        </svg>
                        Back to Optimizer
                    </a>
                    <h1>Optimizer Settings</h1>
                </div>

                {error && (
                    <div className="alert alert-error">
                        {error}
                    </div>
                )}

                {successMessage && (
                    <div className="alert alert-success">
                        {successMessage}
                    </div>
                )}

                <div className="settings-content">
                    <LiveAlgorithmSection
                        config={{
                            GROUPWISE: config.GROUPWISE,
                            PASS_SCHEDULE: config.PASS_SCHEDULE
                        }}
                        onChange={handleLiveChange}
                    />

                    <SharedParametersSection
                        config={{
                            SEARCH_RADIUS: config.SEARCH_RADIUS,
                            TARGET_RADIUS: config.TARGET_RADIUS,
                            SCORES: config.SCORES
                        }}
                        onChange={handleSharedChange}
                    />

                    <GeneticAlgorithmSection
                        config={{
                            GENETIC_ALGORITHM: config.GENETIC_ALGORITHM,
                            MUTATION_STRATEGIES: config.MUTATION_STRATEGIES
                        }}
                        onChange={handleGAChange}
                        onError={setHasValidationError}
                    />
                </div>

                <div className="settings-footer">
                    <button
                        className="btn btn-secondary"
                        onClick={loadConfig}
                        disabled={saving}
                    >
                        Reset
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleSave}
                        disabled={saving || hasValidationError}
                    >
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </div>
        </div>
    );
}
