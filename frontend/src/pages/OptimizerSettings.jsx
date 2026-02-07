import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import LiveAlgorithmSection from '../components/admin/LiveAlgorithmSection';
import GeometricParametersSection from '../components/GeometricParametersSection';
import GeneticAlgorithmSection from '../components/admin/GeneticAlgorithmSection';
import { optimizerConfigApi } from '../api/optimizerConfig';
import './OptimizerSettings.css';

export default function OptimizerSettings() {
    const [profilesData, setProfilesData] = useState(null);
    const [activeTab, setActiveTab] = useState('live'); // 'live', 'A', 'B', or 'C'
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [activating, setActivating] = useState(false);
    const [error, setError] = useState(null);
    const [hasValidationError, setHasValidationError] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');

    useEffect(() => {
        loadProfiles();
    }, []);

    const loadProfiles = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await optimizerConfigApi.getProfiles();
            setProfilesData(data);
            // Load the current tab's config
            if (activeTab === 'live') {
                setConfig(data.live);
            } else {
                setConfig(data.profiles[activeTab]);
            }
        } catch (err) {
            setError('Failed to load configuration: ' + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    // Update config when tab changes
    const handleSwitchTab = (tabId) => {
        if (profilesData) {
            setActiveTab(tabId);
            if (tabId === 'live') {
                setConfig(profilesData.live);
            } else {
                setConfig(profilesData.profiles[tabId]);
            }
            setSuccessMessage('');
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

            if (activeTab === 'live') {
                // Save live config
                await optimizerConfigApi.updateConfig(config);
                // Update local state
                const newData = { ...profilesData };
                newData.live = config;
                setProfilesData(newData);
                setSuccessMessage('Live configuration saved successfully!');
            } else {
                // Save profile config
                await optimizerConfigApi.updateProfile(activeTab, config);
                // Update local state copy
                const newData = { ...profilesData };
                newData.profiles[activeTab] = config;
                setProfilesData(newData);
                setSuccessMessage(`Profile ${activeTab} saved successfully!`);
            }

            setTimeout(() => setSuccessMessage(''), 3000);
        } catch (err) {
            setError('Failed to save configuration: ' + (err.response?.data?.detail || err.message));
        } finally {
            setSaving(false);
        }
    };

    const handleActivate = async () => {
        try {
            setActivating(true);
            setError(null);
            const result = await optimizerConfigApi.activateProfile(activeTab);

            // Update local state to reflect new active profile
            const newData = { ...profilesData };
            newData.active_profile = result.active_profile;
            setProfilesData(newData);

            setSuccessMessage(`Profile ${activeTab} is now ACTIVE!`);
            setTimeout(() => setSuccessMessage(''), 5000);
        } catch (err) {
            setError('Failed to activate profile: ' + (err.response?.data?.detail || err.message));
        } finally {
            setActivating(false);
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
            WEIGHTS: updatedSharedConfig.WEIGHTS
        });
    };

    const handleGAChange = (updatedGAConfig) => {
        setConfig({
            ...config,
            GENETIC_ALGORITHM: updatedGAConfig.GENETIC_ALGORITHM,
            MUTATION_STRATEGIES: updatedGAConfig.MUTATION_STRATEGIES,
            SCOREBOARD: updatedGAConfig.SCOREBOARD
        });
    };

    if (loading) {
        return (
            <div className="maintenance-page-container">
                <div className="maintenance-content-card">
                    <div className="loading-spinner">Loading profiles...</div>
                </div>
            </div>
        );
    }

    if (!profilesData || !config) {
        return (
            <div className="maintenance-page-container">
                <div className="maintenance-content-card">
                    <div className="error-message">{error || 'Failed to load configuration'}</div>
                </div>
            </div>
        );
    }

    const isActive = profilesData.active_profile === activeTab;

    return (
        <div className="maintenance-page-container">
            <div className="maintenance-content-card">
                <div className="admin-header">
                    <div className="header-left">
                        <Link to="/admin/optimizer" className="back-link" title="Back to Optimizer">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                            </svg>
                        </Link>
                        <h1>Optimizer Settings</h1>
                    </div>

                    <div className="profile-tabs" style={{ display: 'flex', gap: '5px', marginLeft: '2rem' }}>
                        {['live', 'A', 'B', 'C'].map(tabId => (
                            <button
                                key={tabId}
                                className={`profile-tab-btn ${activeTab === tabId ? 'active' : ''}`}
                                onClick={() => handleSwitchTab(tabId)}
                                style={{
                                    padding: '8px 24px',
                                    border: '1px solid var(--color-border)',
                                    borderRadius: '4px 4px 0 0',
                                    backgroundColor: activeTab === tabId ? 'var(--color-bg-primary)' : 'var(--color-bg-tertiary)',
                                    color: activeTab === tabId ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                                    cursor: 'pointer',
                                    fontWeight: '600',
                                    position: 'relative',
                                    borderBottom: activeTab === tabId ? '2px solid var(--color-primary)' : '1px solid var(--color-border)'
                                }}
                            >
                                {tabId === 'live' ? 'Live Timeline' : `Profile ${tabId}`}
                                {tabId !== 'live' && profilesData.active_profile === tabId && (
                                    <span style={{
                                        position: 'absolute',
                                        top: '-8px',
                                        right: '-8px',
                                        backgroundColor: '#22c55e',
                                        color: 'white',
                                        fontSize: '0.6rem',
                                        padding: '2px 6px',
                                        borderRadius: '10px',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
                                    }}>ACTIVE</span>
                                )}
                            </button>
                        ))}
                    </div>
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

                <div style={{ flex: 1, overflowY: 'auto', paddingRight: '10px', paddingTop: '1rem' }}>
                    {activeTab !== 'live' && (
                        <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--color-bg-tertiary)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                            <div>
                                <h3 style={{ margin: 0 }}>Editing Profile {activeTab}</h3>
                                <p style={{ margin: '5px 0 0 0', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                                    {isActive ? 'This profile is currently active in the optimizer.' : 'Save changes before activating this profile.'}
                                </p>
                            </div>
                            {!isActive && (
                                <button
                                    className="btn btn-primary"
                                    onClick={handleActivate}
                                    disabled={activating || saving}
                                    style={{ backgroundColor: '#22c55e', borderColor: '#22c55e' }}
                                >
                                    {activating ? 'Activating...' : `Activate Profile ${activeTab}`}
                                </button>
                            )}
                            {isActive && (
                                <div style={{ color: '#22c55e', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <i className="bi bi-check-circle-fill"></i> Currently Active
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'live' ? (
                        <>
                            <LiveAlgorithmSection
                                config={{
                                    GROUPWISE: config.GROUPWISE,
                                    SCOREBOARD: config.SCOREBOARD,
                                    PASS_SCHEDULE: config.PASS_SCHEDULE
                                }}
                                onChange={handleLiveChange}
                            />

                            <GeometricParametersSection
                                config={config}
                                onChange={handleSharedChange}
                            />
                        </>
                    ) : (
                        <>
                            <GeneticAlgorithmSection
                                config={{
                                    GENETIC_ALGORITHM: config.GENETIC_ALGORITHM,
                                    MUTATION_STRATEGIES: config.MUTATION_STRATEGIES,
                                    SCOREBOARD: config.SCOREBOARD
                                }}
                                onChange={handleGAChange}
                                onError={setHasValidationError}
                            />

                            <GeometricParametersSection
                                config={config}
                                onChange={handleSharedChange}
                            />
                        </>
                    )}
                </div>

                <div className="settings-footer" style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--color-border)' }}>
                    <button
                        className="btn btn-secondary"
                        onClick={loadProfiles}
                        disabled={saving || activating}
                    >
                        Reset {activeTab === 'live' ? 'Live' : `Profile ${activeTab}`}
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={handleSave}
                        disabled={saving || activating || hasValidationError}
                    >
                        {saving ? 'Saving...' : `Save ${activeTab === 'live' ? 'Live' : `Profile ${activeTab}`}`}
                    </button>
                </div>
            </div>
        </div>
    );
}
