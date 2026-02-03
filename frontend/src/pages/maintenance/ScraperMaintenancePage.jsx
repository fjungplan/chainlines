import { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Button from '../../components/common/Button';
import { scraperApi } from '../../api/scraper';
import { useAuth } from '../../contexts/AuthContext';
import { formatDateTime } from '../../utils/dateUtils';
import './ScraperMaintenancePage.css';

const ScraperMaintenancePage = () => {
    const navigate = useNavigate();
    const { user, isAdmin } = useAuth();

    // Form State
    const [phase, setPhase] = useState(0); // 0 = All Phases
    const [tier, setTier] = useState("all");
    const [startYear, setStartYear] = useState(2026);
    const [endYear, setEndYear] = useState(2020);
    const [resume, setResume] = useState(false);
    const [dryRun, setDryRun] = useState(false);
    const [isLocked, setIsLocked] = useState(false); // Locked when Resuming

    // Run State
    const [activeRun, setActiveRun] = useState(null);
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);
    const [runs, setRuns] = useState([]);

    // Derived State
    const isRunning = !!activeRun;

    // Modal State
    const [showLogModal, setShowLogModal] = useState(false);
    const [selectedRunId, setSelectedRunId] = useState(null);
    const [selectedRunMetadata, setSelectedRunMetadata] = useState(null);
    const [logContent, setLogContent] = useState("");
    const [loadingLog, setLoadingLog] = useState(false);
    const logContainerRef = useRef(null);

    // Live Log Polling
    useEffect(() => {
        let interval;
        const fetchLogs = async () => {
            if (!selectedRunId) return;
            try {
                const content = await scraperApi.getRunLogs(selectedRunId);
                setLogContent(content);
            } catch (err) {
                // Ignore error, log file might not exist yet
            } finally {
                setLoadingLog(false);
            }
        };

        if (showLogModal && selectedRunId) {
            setLoadingLog(true);
            // Initial fetch
            fetchLogs();
            // Poll every 2s
            interval = setInterval(fetchLogs, 2000);
        }
        return () => clearInterval(interval);
    }, [showLogModal, selectedRunId]);

    // Auto-scroll logs
    useEffect(() => {
        if (showLogModal && logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [logContent, showLogModal]);

    // Resume Logic
    useEffect(() => {
        if (resume) {
            scraperApi.getCheckpoint()
                .then(data => {
                    // Auto-fill and lock
                    if (data.tier) setTier(data.tier);
                    if (data.start_year) setStartYear(data.start_year);
                    if (data.end_year) setEndYear(data.end_year);
                    if (data.phase) setPhase(data.phase);
                    setIsLocked(true);
                })
                .catch(err => {
                    setResume(false);
                    setError("No active checkpoint found to resume.");
                    setTimeout(() => setError(null), 3000);
                });
        } else {
            setIsLocked(false);
        }
    }, [resume]);

    // Fetch Runs
    const fetchRuns = async () => {
        try {
            // Fetch top 100 latest runs
            const data = await scraperApi.getRuns(0, 100);
            setRuns(data?.items || []);

            // Find actively running or paused task
            let current = data?.items?.find(r => ['RUNNING', 'PAUSED', 'PENDING'].includes(r.status));

            // If no active run, check if the most recent run finished very recently (e.g., < 30 seconds ago)
            if (!current && data?.items?.length > 0) {
                const latest = data.items[0];
                const finishTime = latest.ended_at ? new Date(latest.ended_at).getTime() : 0;
                const now = new Date().getTime();
                if (now - finishTime < 30000) {
                    current = latest;
                }
            }
            setActiveRun(current || null);

            // Poll faster if active
            if (current && ['RUNNING', 'PAUSED', 'PENDING'].includes(current.status)) {
                setTimeout(fetchRuns, 2000);
            }
        } catch (err) {
            console.error("Failed to fetch runs", err);
        }
    };

    useEffect(() => {
        fetchRuns();
    }, []);

    const handleStart = async () => {
        setError(null);
        setMessage(null);
        try {
            await scraperApi.startScraper({
                phase: parseInt(phase),
                tier: tier,
                start_year: parseInt(startYear),
                end_year: parseInt(endYear),
                resume: resume,
                dry_run: dryRun
            });
            // Immediate fetch to catch the new run
            setTimeout(fetchRuns, 500);
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to start scraper");
        }
    };

    const handlePause = async () => {
        try {
            await scraperApi.pauseScraper();
            fetchRuns();
        } catch (err) {
            setError("Failed to pause scraper");
        }
    };

    const handleResume = async () => {
        try {
            await scraperApi.resumeScraper();
            fetchRuns();
        } catch (err) {
            setError("Failed to resume scraper");
        }
    };

    const handleAbort = async () => {
        if (!window.confirm("Are you sure you want to abort the scraper?")) return;
        try {
            await scraperApi.abortScraper();
            fetchRuns();
        } catch (err) {
            setError("Failed to abort scraper");
        }
    };

    const handleViewLogs = async (runId) => {
        const run = runs.find(r => r.run_id === runId);
        setSelectedRunId(runId);
        setSelectedRunMetadata(run);
        setLogContent("");
        setShowLogModal(true);
        setLoadingLog(true);
        try {
            const content = await scraperApi.getRunLogs(runId);
            setLogContent(content);
        } catch (err) {
            setLogContent("Failed to load logs.");
        } finally {
            setLoadingLog(false);
        }
    };

    if (!isAdmin()) {
        return <div className="maintenance-page-container justify-center text-red-500 font-bold">Access Denied</div>;
    }

    return (
        <div className="maintenance-page-container">
            <div className="maintenance-content-card">
                {/* Header */}
                <div className="admin-header">
                    <div className="header-left">
                        <Link to="/admin" className="back-link" title="Back to Admin Panel">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                            </svg>
                        </Link>
                        <h1>Scraper Maintenance</h1>
                    </div>
                </div>

                {/* Scrollable Content Area */}
                <div className="scraper-scroll-content">
                    {/* Notifications */}
                    {error && <div className="mb-4 p-3 bg-red-900/50 text-red-200 rounded border border-red-700">{error}</div>}

                    {/* Controls & Status Row */}
                    <div className="scraper-controls-row">
                        {/* Left Panel: Execution Parameters */}
                        <div className="execution-params-section">
                            <div className="control-group-header">
                                <h3 className="control-group-title">Execution Parameters</h3>
                                <div className="header-controls">
                                    <label className="control-toggle">
                                        <input
                                            type="checkbox"
                                            checked={resume}
                                            onChange={(e) => setResume(e.target.checked)}
                                            disabled={isRunning}
                                        />
                                        <span>Resume</span>
                                    </label>

                                    <label className="control-toggle">
                                        <input
                                            type="checkbox"
                                            checked={dryRun}
                                            onChange={(e) => setDryRun(e.target.checked)}
                                            disabled={isRunning}
                                        />
                                        <span>Dry Run</span>
                                    </label>
                                </div>
                            </div>

                            <div className="scraper-form-row">
                                <div className="form-group wide-select">
                                    <label>Phase</label>
                                    <select
                                        value={phase}
                                        onChange={(e) => setPhase(parseInt(e.target.value))}
                                        disabled={isLocked || isRunning}
                                    >
                                        <option value={0}>All Phases (Sequential)</option>
                                        <option value={1}>Phase 1: Discovery (Sponsors)</option>
                                        <option value={2}>Phase 2: Assembly (Teams)</option>
                                        <option value={3}>Phase 3: Lineage (History)</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label>Tier</label>
                                    <select
                                        value={tier}
                                        onChange={(e) => setTier(e.target.value)}
                                        disabled={isLocked || isRunning}
                                    >
                                        <option value="all">All Tiers</option>
                                        <option value="1">Tier 1</option>
                                        <option value="2">Tier 2</option>
                                        <option value="3">Tier 3</option>
                                    </select>
                                </div>

                                <div className="form-group year-input">
                                    <label>Start Year</label>
                                    <input
                                        type="number"
                                        value={startYear}
                                        onChange={(e) => setStartYear(e.target.value)}
                                        disabled={isLocked || isRunning}
                                    />
                                </div>

                                <div className="form-group year-input">
                                    <label>End Year</label>
                                    <input
                                        type="number"
                                        value={endYear}
                                        onChange={(e) => setEndYear(e.target.value)}
                                        disabled={isLocked || isRunning}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Right Panel: Scraper Status */}
                        <div className="scraper-status-section">
                            <div className="control-group-header">
                                <h3 className="control-group-title">Scraper Status</h3>
                            </div>

                            <div className="status-display-container">
                                <div className="status-header-row">
                                    {/* Traffic Light & Label Combined */}
                                    <div className="traffic-light">
                                        <div
                                            className={`light ${error ? 'active-red' :
                                                !activeRun ? 'active-gray' :
                                                    activeRun.status === 'PAUSED' ? 'active-amber' :
                                                        activeRun.status === 'FAILED' ? 'active-red' :
                                                            activeRun.status === 'COMPLETED' ? 'active-green-static' :
                                                                ['RUNNING', 'PENDING'].includes(activeRun.status) ? 'active-green' : 'active-gray'
                                                }`}
                                            title={error ? error : (activeRun ? activeRun.status : "IDLE")}
                                        ></div>
                                        <div className="status-label">
                                            {activeRun ? activeRun.status : (error ? "FAILED" : "IDLE")}
                                        </div>
                                    </div>

                                    {activeRun && (
                                        <button
                                            onClick={() => handleViewLogs(activeRun.run_id)}
                                            className="live-output-btn"
                                        >
                                            <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                                                <path d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2zm2-1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H2z" />
                                                <path d="M4 11.794V4.206l6.897 3.794L4 11.794z" />
                                            </svg>
                                            View Logs
                                        </button>
                                    )}
                                </div>

                                <div className="status-controls">
                                    {/* Combined Start/Resume Button */}
                                    {activeRun && activeRun.status === 'PAUSED' ? (
                                        <button
                                            className="control-btn btn-resume"
                                            onClick={handleResume}
                                        >
                                            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M12.7 8a.7.7 0 0 0-.2-.6l-9-5A.7.7 0 0 0 2.5 3v10a.7.7 0 0 0 1 .6l9-5z" /></svg>
                                            Resume
                                        </button>
                                    ) : (
                                        <button
                                            className="control-btn btn-start"
                                            onClick={handleStart}
                                            disabled={isRunning}
                                        >
                                            {isRunning ? (
                                                <svg className="animate-spin" width="16" height="16" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                </svg>
                                            ) : (
                                                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M11.596 8.697l-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z" /></svg>
                                            )}
                                            {resume ? 'Resume' : 'Start'}
                                        </button>
                                    )}

                                    <button
                                        className="control-btn btn-pause"
                                        onClick={handlePause}
                                        disabled={!activeRun || activeRun.status !== 'RUNNING'}
                                    >
                                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 3.5A1.5 1.5 0 0 1 7 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5zm5 0A1.5 1.5 0 0 1 12 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5z" /></svg>
                                        Pause
                                    </button>

                                    <button
                                        className="control-btn btn-abort"
                                        onClick={handleAbort}
                                        disabled={!activeRun}
                                    >
                                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M2.5 1h11a1.5 1.5 0 0 1 1.5 1.5v11a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 13.5v-11A1.5 1.5 0 0 1 2.5 1z" /></svg>
                                        Stop
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* History Section */}
                    <div className="run-history-section">
                        <div className="control-group-header">
                            <h3 className="control-group-title">Run History</h3>
                        </div>
                        <div className="history-table-container">
                            <table className="history-table">
                                <thead>
                                    <tr>
                                        <th>Started</th>
                                        <th>Phase</th>
                                        <th>Tier</th>
                                        <th className="text-center">Start</th>
                                        <th className="text-center">End</th>
                                        <th className="text-center">Dry Run</th>
                                        <th>Status</th>
                                        <th className="actions-col">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(runs || []).map(run => (
                                        <tr key={run.run_id}>
                                            <td>{formatDateTime(run.started_at)}</td>
                                            <td>{run.phase === 0 ? "All" : run.phase}</td>
                                            <td>{run.tier || "-"}</td>
                                            <td className="text-center">{run.start_year || "-"}</td>
                                            <td className="text-center">{run.end_year || "-"}</td>
                                            <td className="text-center">{run.dry_run ? "Yes" : "No"}</td>
                                            <td>
                                                <span className={`status-badge status-${run.status.toLowerCase()}`}>
                                                    {run.status}
                                                </span>
                                            </td>
                                            <td className="actions-col">
                                                <Button
                                                    variant="secondary"
                                                    size="sm"
                                                    onClick={() => handleViewLogs(run.run_id)}
                                                >
                                                    View
                                                </Button>
                                            </td>
                                        </tr>
                                    ))}
                                    {runs.length === 0 && (
                                        <tr>
                                            <td colSpan="8" className="p-8 text-center text-gray-500">No runs recorded</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            {/* Log Modal */}
            {showLogModal && (
                <div className="modal-overlay">
                    <div className="modal-content log-viewer-modal">
                        <div className="modal-header">
                            <h2>
                                Scraper Execution log - {selectedRunMetadata ? (
                                    <>
                                        {formatDateTime(selectedRunMetadata.started_at)} - {selectedRunMetadata.status}
                                    </>
                                ) : "Loading..."}
                            </h2>
                            <button
                                onClick={() => {
                                    setShowLogModal(false);
                                    setSelectedRunMetadata(null);
                                    setSelectedRunId(null);
                                }}
                                className="close-btn"
                                title="Close"
                            >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="18" y1="6" x2="6" y2="18"></line>
                                    <line x1="6" y1="6" x2="18" y2="18"></line>
                                </svg>
                            </button>
                        </div>
                        <div className="log-modal-body">
                            <div className="log-container" ref={logContainerRef}>
                                <pre>{logContent || "Connecting to live logs..."}</pre>
                            </div>
                        </div>
                        <div className="modal-footer">
                            <Button variant="secondary" onClick={() => {
                                setShowLogModal(false);
                                setSelectedRunMetadata(null);
                                setSelectedRunId(null);
                            }}>Close Viewer</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ScraperMaintenancePage;
