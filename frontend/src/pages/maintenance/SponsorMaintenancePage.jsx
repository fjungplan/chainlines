import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { sponsorsApi } from '../../api/sponsors';
import { LoadingSpinner } from '../../components/Loading';
import { ErrorDisplay } from '../../components/ErrorDisplay';
import './SponsorMaintenancePage.css';
import SponsorMasterEditor from '../../components/maintenance/SponsorMasterEditor';
import Button from '../../components/common/Button';

export default function SponsorMaintenancePage() {
    const { user, isEditor, isAdmin } = useAuth();
    const [searchParams, setSearchParams] = useSearchParams();

    const [masters, setMasters] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');

    // Editor State
    const [isEditorOpen, setIsEditorOpen] = useState(false);
    const [selectedMasterId, setSelectedMasterId] = useState(null); // null = Create Mode

    // Deep Link: Check for ?edit=ID on mount
    useEffect(() => {
        const editId = searchParams.get('edit');
        if (editId) {
            setSelectedMasterId(editId);
            setIsEditorOpen(true);
            // Clear the param so back navigation doesn't re-trigger
            setSearchParams({}, { replace: true });
        }
    }, []);

    const fetchMasters = async () => {
        setLoading(true);
        setError(null);
        try {
            let data;
            if (searchQuery.trim().length > 0) {
                data = await sponsorsApi.searchMasters(searchQuery);
            } else {
                data = await sponsorsApi.getAllMasters();
            }
            setMasters(data);
        } catch (err) {
            console.error("Failed to fetch sponsors:", err);
            setError("Failed to load sponsors. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    // Debounced search
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchMasters();
        }, 500);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const handleCreate = () => {
        setSelectedMasterId(null);
        setIsEditorOpen(true);
    };

    const handleEdit = (masterId) => {
        setSelectedMasterId(masterId);
        setIsEditorOpen(true);
    };

    const handleEditorClose = () => {
        setIsEditorOpen(false);
        setSelectedMasterId(null);
        fetchMasters(); // Refetch to prevent stale data
    };

    const handleEditorSuccess = (newMasterId) => {
        if (newMasterId) {
            // Stay open and switch to Edit Mode for the new master
            setSelectedMasterId(newMasterId);
            fetchMasters();
        } else {
            // Close
            handleEditorClose();
            fetchMasters();
        }
    };

    if (!user) return <div className="sponsor-page-container">Please log in.</div>;

    return (
        <div className="maintenance-page-container">
            {isEditorOpen ? (
                <SponsorMasterEditor
                    masterId={selectedMasterId}
                    onClose={handleEditorClose}
                    onSuccess={handleEditorSuccess}
                />
            ) : (
                <div className="maintenance-content-card">
                    <div className="sponsor-header">
                        <h1>Sponsor Maintenance</h1>
                    </div>

                    <div className="sponsor-controls">
                        <input
                            type="text"
                            placeholder="Search sponsors (e.g. Visma, Ineos)..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        // removed search-input class to rely on global
                        // className="search-input" 
                        />
                        {(isEditor() || isAdmin()) && (
                            <Button variant="primary" onClick={handleCreate}>
                                + Create New Sponsor
                            </Button>
                        )}
                    </div>

                    {loading ? (
                        <LoadingSpinner message="Loading sponsors..." />
                    ) : error ? (
                        <ErrorDisplay error={error} onRetry={fetchMasters} />
                    ) : (
                        <div className="sponsor-list">
                            {masters.length === 0 ? (
                                <div className="empty-state">No sponsors found.</div>
                            ) : (
                                <table className="sponsor-table">
                                    <thead>
                                        <tr>
                                            <th>Legal Name</th>
                                            <th>Industry</th>
                                            <th>Brands</th>
                                            <th className="actions-col">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {masters.map(master => (
                                            <tr key={master.master_id}>
                                                <td>
                                                    <div className="master-name">{master.legal_name}</div>
                                                    {master.is_protected && <span className="protected-badge" title="Protected Record">🛡️</span>}
                                                </td>
                                                <td>{master.industry_sector || '-'}</td>
                                                <td>{master.brand_count}</td>
                                                <td className="actions-col">
                                                    <Button
                                                        variant="secondary"
                                                        size="sm"
                                                        onClick={() => handleEdit(master.master_id)}
                                                        disabled={!isEditor() && !isAdmin()}
                                                    >
                                                        Edit
                                                    </Button>
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
