import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import CenteredPageLayout from '../../components/layout/CenteredPageLayout';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';
import { scraperApi } from '../../api/scraper';
import { useAuth } from '../../hooks/useAuth';

const ScraperMaintenancePage = () => {
    const navigate = useNavigate();
    const { user, isSuperAdmin } = useAuth();

    // Form State
    const [phase, setPhase] = useState(0); // 0 = All Phases
    const [tier, setTier] = useState("all");
    const [startYear, setStartYear] = useState(2025);
    const [endYear, setEndYear] = useState(1990);
    const [resume, setResume] = useState(false);
    const [dryRun, setDryRun] = useState(false);
    const [isLocked, setIsLocked] = useState(false); // Locked when Resuming

    // Run State
    const [isRunning, setIsRunning] = useState(false);
    const [message, setMessage] = useState(null);
    const [error, setError] = useState(null);
    const [runs, setRuns] = useState([]);
    const [totalRuns, setTotalRuns] = useState(0);
    const [page, setPage] = useState(0);

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
                    // Phase is tricky, checkpoint stores current phase implementation detail
                    // We assume user resumes the phase they were in? 
                    // Actually, checkpoint data.phase is useful.
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
            const data = await scraperApi.getRuns(page * 10, 10);
            setRuns(data.items);
            setTotalRuns(data.total);

            // Check if any is RUNNING, if so poll?
            const anyRunning = data.items.some(r => r.status === 'RUNNING' || r.status === 'PENDING');
            if (anyRunning) {
                setTimeout(fetchRuns, 5000); // Poll every 5s
            }
        } catch (err) {
            console.error("Failed to fetch runs", err);
        }
    };

    useEffect(() => {
        fetchRuns();
    }, [page]);

    const handleStart = async () => {
        setIsRunning(true);
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
            setMessage("Scraper started successfully in background.");
            fetchRuns();
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to start scraper");
        } finally {
            setIsRunning(false);
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

    if (!isSuperAdmin()) {
        return <div className="p-8 text-center text-red-500">Access Denied</div>;
    }

    return (
        <CenteredPageLayout title="Scraper Maintenance">
            <div className="flex justify-start mb-6">
                <Button variant="secondary" onClick={() => navigate('/admin')}>
                    ← Back to Admin
                </Button>
            </div>

            <Card className="mb-6">
                <h2 className="text-xl font-bold mb-4 text-white">Scraper Controls</h2>

                {error && <div className="mb-4 p-3 bg-red-900/50 text-red-200 rounded border border-red-700">{error}</div>}
                {message && <div className="mb-4 p-3 bg-green-900/50 text-green-200 rounded border border-green-700">{message}</div>}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    {/* Left Column: Core Params */}
                    <div className="space-y-4">
                        <div>
                            <label className="block text-gray-400 mb-1">Phase</label>
                            <select
                                value={phase}
                                onChange={(e) => setPhase(parseInt(e.target.value))}
                                disabled={isLocked || isRunning}
                                className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                            >
                                <option value={0}>All Phases (Sequential)</option>
                                <option value={1}>Phase 1: Discovery (Sponsors)</option>
                                <option value={2}>Phase 2: Assembly (Teams)</option>
                                <option value={3}>Phase 3: Lineage (History)</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-gray-400 mb-1">Tier</label>
                            <select
                                value={tier}
                                onChange={(e) => setTier(e.target.value)}
                                disabled={isLocked || isRunning}
                                className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                            >
                                <option value="all">All Tiers</option>
                                <option value="1">Tier 1 (WorldTour)</option>
                                <option value="2">Tier 2 (ProTeam)</option>
                                <option value="3">Tier 3 (Continental)</option>
                            </select>
                        </div>
                    </div>

                    {/* Right Column: Range & Options */}
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-gray-400 mb-1">Start Year</label>
                                <input
                                    type="number"
                                    value={startYear}
                                    onChange={(e) => setStartYear(e.target.value)}
                                    disabled={isLocked || isRunning}
                                    className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-gray-400 mb-1">End Year</label>
                                <input
                                    type="number"
                                    value={endYear}
                                    onChange={(e) => setEndYear(e.target.value)}
                                    disabled={isLocked || isRunning}
                                    className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white"
                                />
                            </div>
                        </div>

                        <div className="flex space-x-6 pt-2">
                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={resume}
                                    onChange={(e) => setResume(e.target.checked)}
                                    disabled={isRunning}
                                    className="w-4 h-4 rounded border-gray-600 bg-slate-800 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-900"
                                />
                                <span className={resume ? "text-blue-400 font-medium" : "text-gray-400"}>Resume Checkpoint</span>
                            </label>

                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={dryRun}
                                    onChange={(e) => setDryRun(e.target.checked)}
                                    disabled={isRunning}
                                    className="w-4 h-4 rounded border-gray-600 bg-slate-800 text-amber-500 focus:ring-amber-500 focus:ring-offset-slate-900"
                                />
                                <span className={dryRun ? "text-amber-400 font-medium" : "text-gray-400"}>Dry Run (Log Only)</span>
                            </label>
                        </div>
                    </div>
                </div>

                <div className="flex justify-end pt-4 border-t border-slate-700">
                    <Button onClick={handleStart} disabled={isRunning} isLoading={isRunning}>
                        {resume ? 'Resume Scraper' : 'Start Scraper'}
                    </Button>
                </div>
            </Card>

            <Card>
                <h3 className="text-lg font-bold mb-4 text-white">Run History</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="text-gray-400 border-b border-slate-700">
                                <th className="p-3">Started</th>
                                <th className="p-3">Phase</th>
                                <th className="p-3">Tier</th>
                                <th className="p-3">Range</th>
                                <th className="p-3">Status</th>
                                <th className="p-3">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700">
                            {runs.map(run => (
                                <tr key={run.run_id} className="text-gray-300 hover:bg-slate-800/50">
                                    <td className="p-3">{new Date(run.started_at).toLocaleString()}</td>
                                    <td className="p-3">{run.phase === 0 ? "All" : run.phase}</td>
                                    <td className="p-3">{run.tier || "-"}</td>
                                    <td className="p-3">{run.start_year ? `${run.start_year}-${run.end_year}` : "N/A"}</td>
                                    <td className="p-3">
                                        <span className={`px-2 py-1 rounded text-xs font-bold ${run.status === 'COMPLETED' ? 'bg-green-900 text-green-300' :
                                                run.status === 'FAILED' ? 'bg-red-900 text-red-300' :
                                                    run.status === 'RUNNING' ? 'bg-blue-900 text-blue-300 animate-pulse' :
                                                        'bg-gray-700 text-gray-300'
                                            }`}>
                                            {run.status}
                                        </span>
                                    </td>
                                    <td className="p-3">
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

                {/* Pagination (Simple) */}
                <div className="flex justify-between items-center mt-4 text-sm text-gray-400">
                    <span>Page {page + 1}</span>
                    <div className="space-x-2">
                        <button
                            disabled={page === 0}
                            onClick={() => setPage(p => Math.max(0, p - 1))}
                            className="px-3 py-1 bg-slate-800 rounded hover:bg-slate-700 disabled:opacity-50"
                        >
                            Previous
                        </button>
                        <button
                            disabled={(page + 1) * 10 >= totalRuns}
                            onClick={() => setPage(p => p + 1)}
                            className="px-3 py-1 bg-slate-800 rounded hover:bg-slate-700 disabled:opacity-50"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </Card>

            {/* Log Modal */}
            {showLogModal && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
                    <div className="bg-slate-900 rounded-lg w-full max-w-4xl max-h-[90vh] flex flex-col border border-slate-700 shadow-2xl">
                        <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800 rounded-t-lg">
                            <h3 className="font-bold text-white">Execution Logs</h3>
                            <button
                                onClick={() => setShowLogModal(false)}
                                className="text-gray-400 hover:text-white"
                            >
                                ✕
                            </button>
                        </div>
                        <div className="flex-1 overflow-auto p-4 bg-black font-mono text-xs text-green-400">
                            <pre>{logContent}</pre>
                        </div>
                        <div className="p-4 border-t border-slate-700 bg-slate-800 rounded-b-lg flex justify-end">
                            <Button variant="secondary" onClick={() => setShowLogModal(false)}>Close</Button>
                        </div>
                    </div>
                </div>
            )}
        </CenteredPageLayout>
    );
};

export default ScraperMaintenancePage;
