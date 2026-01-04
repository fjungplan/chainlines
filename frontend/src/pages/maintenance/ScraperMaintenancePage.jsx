import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Button from '../../components/common/Button';
import { scraperApi } from '../../api/scraper';
import { useAuth } from '../../contexts/AuthContext';
import './ScraperMaintenancePage.css';

const ScraperMaintenancePage = () => {
    const navigate = useNavigate();
    const { user, isAdmin } = useAuth();

    // Form State
    const [phase, setPhase] = useState(0); // 0 = All Phases
    const [tier, setTier] = useState("all");
    const [startYear, setStartYear] = useState(2025);
    const [endYear, setEndYear] = useState(1990);
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
    const [logContent, setLogContent] = useState("");
    const [loadingLog, setLoadingLog] = useState(false);

    // Checkpoint Logic
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
                    setMessage(`Resuming implementation from ${data.last_updated}`);
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
            setRuns(data.items);

            // Find actively running or paused task
            const current = data.items.find(r => ['RUNNING', 'PAUSED', 'PENDING'].includes(r.status));
            setActiveRun(current || null);

            // Poll faster if active
            if (current) {
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
            setMessage("Scraper started successfully.");
            // Immediate fetch to catch the new run
            setTimeout(fetchRuns, 500);
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to start scraper");
        }
    };

    const handlePause = async () => {
        try {
            await scraperApi.pauseScraper();
            setMessage("Signal sent: Pause");
            fetchRuns();
        } catch (err) {
            setError("Failed to pause scraper");
        }
    };

    const handleResume = async () => {
        try {
            await scraperApi.resumeScraper();
            setMessage("Signal sent: Resume");
            fetchRuns();
        } catch (err) {
            setError("Failed to resume scraper");
        }
    };

    const handleAbort = async () => {
        if (!window.confirm("Are you sure you want to abort the scraper?")) return;
        try {
            await scraperApi.abortScraper();
            setMessage("Signal sent: Abort");
            fetchRuns();
        } catch (err) {
            setError("Failed to abort scraper");
        }
    };

    const handleViewLogs = async (runId) => {
        setShowLogModal(true);
        setLoadingLog(true);
        setLogContent("Loading...");
        try {
            const content = await scraperApi.getRunLogs(runId);
            setLogContent(content);
        } catch (err) {
            setLogContent("Failed to load logs. Log file may be missing.");
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
                <div className="scraper-header">
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
                    {message && <div className="mb-4 p-3 bg-green-900/50 text-green-200 rounded border border-green-700">{message}</div>}

                    {/* Controls Section */}
                    {/* Controls Section - Split View */}
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

                            <div className="flex justify-end pt-4 mt-auto border-t border-slate-700">
                                <Button onClick={handleStart} disabled={isRunning} isLoading={isRunning}>
                                    {resume ? 'Resume Scraper' : 'Start Scraper'}
                                </Button>
                            </div>
                        </div>

                        {/* Right Panel: Scraper Status */}
                        <div className="scraper-status-section">
                            <div className="control-group-header">
                                <h3 className="control-group-title">Scraper Status</h3>
                            </div>

                            <div className="status-display-container">
                                {/* Traffic Light & Label Combined */}
                                <div className="traffic-light">
                                    <div
                                        className={`light ${!activeRun ? 'active-red' :
                                                activeRun.status === 'PAUSED' ? 'active-amber' :
                                                    ['RUNNING', 'PENDING'].includes(activeRun.status) ? 'active-green' : 'active-gray'
                                            }`}
                                        title={activeRun ? activeRun.status : "STOPPED"}
                                    ></div>
                                    <div className="status-label">
                                        {activeRun ? activeRun.status : "IDLE"}
                                    </div>
                                </div>

                                <div className="status-controls">
                                    <button
                                        className="control-btn btn-pause"
                                        onClick={handlePause}
                                        disabled={!activeRun || activeRun.status !== 'RUNNING'}
                                    >
                                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 3.5A1.5 1.5 0 0 1 7 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5zm5 0A1.5 1.5 0 0 1 12 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5z" /></svg>
                                        Pause
                                    </button>
                                    <button
                                        className="control-btn btn-resume"
                                        onClick={handleResume}
                                        disabled={!activeRun || activeRun.status !== 'PAUSED'}
                                    >
                                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M12.7 8a.7.7 0 0 0-.2-.6l-9-5A.7.7 0 0 0 2.5 3v10a.7.7 0 0 0 1 .6l9-5z" /></svg>
                                        Resume
                                    </button>
                                    <button
                                        className="control-btn btn-abort"
                                        onClick={handleAbort}
                                        disabled={!activeRun}
                                    >
                                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M2.5 1h11a1.5 1.5 0 0 1 1.5 1.5v11a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 13.5v-11A1.5 1.5 0 0 1 2.5 1z" /></svg>
                                        Abort
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

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
                                        <th>Range</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {runs.map(run => (
                                        <tr key={run.run_id}>
                                            <td>{new Date(run.started_at).toLocaleString()}</td>
                                            <td>{run.phase === 0 ? "All" : run.phase}</td>
                                            <td>{run.tier || "-"}</td>
                                            <td>{run.start_year ? `${run.start_year}-${run.end_year}` : "N/A"}</td>
                                            <td>
                                                <span className={`status-badge status-${run.status.toLowerCase()}`}>
                                                    {run.status}
                                                </span>
                                            </td>
                                            <td>
                                                <button
                                                    onClick={() => handleViewLogs(run.run_id)}
                                                    className="text-sm text-blue-400 hover:text-blue-300 underline"
                                                >
                                                    View Logs
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {runs.length === 0 && (
                                        <tr>
                                            <td colSpan="6" className="p-8 text-center text-gray-500">No runs recorded</td>
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
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
                    <div className="bg-slate-900 rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col border border-slate-700 shadow-2xl">
                        <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800 rounded-t-lg">
                            <h3 className="font-bold text-white mb-0">Execution Logs</h3>
                            <button
                                onClick={() => setShowLogModal(false)}
                                className="text-gray-400 hover:text-white"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="log-modal-content">
                            <pre>{logContent}</pre>
                        </div>
                        <div className="p-4 border-t border-slate-700 bg-slate-800 rounded-b-lg flex justify-end">
                            <Button variant="secondary" onClick={() => setShowLogModal(false)}>Close</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ScraperMaintenancePage;
