import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { teamsApi } from '../api/teams';
import { LoadingSpinner } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import './TeamMaintenancePage.css'; // Global Team Page styles (List grid etc)
// Note: Editor styles are handled within TeamNodeEditor/TeamEraEditor via imported SponsorEditor.css

import TeamNodeEditor from '../components/maintenance/TeamNodeEditor';
import TeamEraEditor from '../components/maintenance/TeamEraEditor';

export default function TeamMaintenancePage() {
    const { user, isEditor, isAdmin } = useAuth();

    // View State
    const [viewMode, setViewMode] = useState('list'); // 'list' | 'node' | 'era'
    const [selectedNodeId, setSelectedNodeId] = useState(null);
    const [selectedEraId, setSelectedEraId] = useState(null);

    // List State
    const [teams, setTeams] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');

    const fetchTeams = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await teamsApi.getTeams({ limit: 100 });
            setTeams(data.items);
            setTotal(data.total);
        } catch (err) {
            console.error("Failed to fetch teams:", err);
            setError("Failed to load teams. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTeams();
    }, []);

    // --- Actions ---

    const handleCreateTeam = () => {
        setSelectedNodeId(null);
        setViewMode('node');
    };

    const handleEditTeam = (nodeId) => {
        setSelectedNodeId(nodeId);
        setViewMode('node');
    };

    const handleBackToList = () => {
        setViewMode('list');
        setSelectedNodeId(null);
        setSelectedEraId(null);
        fetchTeams();
    };

    // Called when Team Node is saved (create or update)
    const handleNodeSuccess = (newNodeId) => {
        if (newNodeId) setSelectedNodeId(newNodeId);
        // If we want to stay in 'node' view, we do nothing else.
        // If we wanted to close, we'd call handleBackToList().
        // The Editor handles "Save & Close" vs "Save".
        // if "Save & Close" was clicked, Editor calls onClose -> handleBackToList.
        // if "Save", Editor stays open.
        // Wait, Editor calls onSuccess with ID. 
        // We need to know if we should close or not? 
        // The Editor handles that logic internally? No, Editor prop says `onClose` and `onSuccess`.
        // My Editor impl: `if (shouldClose) onClose()`. 
        // So `onClose` is "Back to List". `onSuccess` is "Update ID in parent".

        // Actually, for creation, we need to switch from "Create Mode" (null ID) to "Edit Mode" (new ID).
        if (newNodeId && !selectedNodeId) {
            setSelectedNodeId(newNodeId);
        }
    };

    // --- Era Navigation ---

    const handleEraSelect = (eraId) => {
        // Switch to Level 3
        setSelectedEraId(eraId);
        setViewMode('era');
    };

    const handleBackToNode = () => {
        // Back from Level 3 to Level 2
        setViewMode('node');
        setSelectedEraId(null);
    };

    const handleEraSuccess = (newEraId) => {
        // If searching/switching within Era Editor:
        if (newEraId) {
            setSelectedEraId(newEraId);
            // Ensure we stay in era view?
            setViewMode('era');
        } else {
            // If passed empty/undefined, means "Back" or "Done"
            handleBackToNode();
        }
    };


    if (!user) return <div className="team-page-container">Please log in.</div>;

    // --- Render ---

    return (
        <div className="team-page-container">
            {viewMode === 'node' ? (
                <TeamNodeEditor
                    nodeId={selectedNodeId}
                    onClose={handleBackToList}
                    onSuccess={handleNodeSuccess}
                    onEraSelect={handleEraSelect}
                />
            ) : viewMode === 'era' ? (
                <TeamEraEditor
                    eraId={selectedEraId}
                    nodeId={selectedNodeId}
                    onSuccess={handleEraSuccess}
                    onDelete={handleBackToNode}
                />
            ) : (
                <div className="team-inner-container">
                    <div className="team-header">
                        <h1>Team Maintenance</h1>
                    </div>

                    <div className="team-controls">
                        <input
                            type="text"
                            placeholder="Search teams..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="team-search-input"
                            disabled
                        />
                        {(isEditor() || isAdmin()) && (
                            <button className="primary-button" onClick={handleCreateTeam}>
                                + Create New Team
                            </button>
                        )}
                    </div>

                    {loading ? (
                        <LoadingSpinner message="Loading teams..." />
                    ) : error ? (
                        <ErrorDisplay error={error} onRetry={fetchTeams} />
                    ) : (
                        <div className="team-list">
                            {teams.length === 0 ? (
                                <div className="empty-state">No teams found.</div>
                            ) : (
                                <table className="team-table">
                                    <thead>
                                        <tr>
                                            <th>Legal Name</th>
                                            <th>Founding Year</th>
                                            <th>Dissolution</th>
                                            <th>Active</th>
                                            <th>Current Tier</th>
                                            <th className="actions-col">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {teams.map(team => (
                                            <tr key={team.node_id}>
                                                <td>
                                                    <div className="team-name">{team.legal_name}</div>
                                                    {team.is_protected && <span className="protected-badge" title="Protected Record">🛡️</span>}
                                                </td>
                                                <td>{team.founding_year}</td>
                                                <td>{team.dissolution_year || '-'}</td>
                                                <td>{team.is_active ? 'Yes' : 'No'}</td>
                                                <td>{team.current_tier || '-'}</td>
                                                <td className="actions-col">
                                                    <button
                                                        className="edit-button"
                                                        onClick={() => handleEditTeam(team.node_id)}
                                                        disabled={!isEditor() && !isAdmin()}
                                                    >
                                                        Edit
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
