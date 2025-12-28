import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { getUsers } from '../../api/users';
import { LoadingSpinner } from '../../components/Loading';
import { ErrorDisplay } from '../../components/ErrorDisplay';
import Button from '../../components/common/Button';
import UserEditor from '../../components/maintenance/UserEditor';
import { useDebounce } from '../../hooks/useDebounce';
import './UserMaintenancePage.css';

export default function UserMaintenancePage() {
    const { isAdmin } = useAuth();

    // View State
    const [viewMode, setViewMode] = useState('list'); // 'list' | 'editor'
    const [selectedUser, setSelectedUser] = useState(null); // Pass entire user object

    // List State
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const debouncedSearch = useDebounce(searchQuery, 500);

    // Sorting State
    const [sortConfig, setSortConfig] = useState({ key: 'display_name', direction: 'asc' });

    const fetchUsers = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getUsers({ search: debouncedSearch, limit: 100 });
            setUsers(data.items);
        } catch (err) {
            console.error("Failed to fetch users:", err);
            setError("Failed to load users. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isAdmin()) {
            fetchUsers();
        }
    }, [debouncedSearch]);

    // --- Sorting Logic ---
    const handleSort = (key) => {
        setSortConfig(prev => ({
            key,
            direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
        }));
    };

    const sortedUsers = [...users].sort((a, b) => {
        const { key, direction } = sortConfig;
        let valA = a[key];
        let valB = b[key];

        if (typeof valA === 'string') valA = valA.toLowerCase();
        if (typeof valB === 'string') valB = valB.toLowerCase();
        if (valA === null || valA === undefined) valA = '';
        if (valB === null || valB === undefined) valB = '';

        if (valA < valB) return direction === 'asc' ? -1 : 1;
        if (valA > valB) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    // --- Actions ---
    const handleEditUser = (user) => {
        setSelectedUser(user);
        setViewMode('editor');
    };

    const handleBackToList = () => {
        setViewMode('list');
        setSelectedUser(null);
        fetchUsers();
    };

    const handleEditorSuccess = () => {
        handleBackToList();
    };

    if (!isAdmin()) return <div className="maintenance-page-container">Access Denied</div>;

    // --- Render ---
    return (
        <div className="maintenance-page-container">
            {viewMode === 'editor' ? (
                <UserEditor
                    user={selectedUser}
                    onClose={handleBackToList}
                    onSuccess={handleEditorSuccess}
                />
            ) : (
                <div className="maintenance-content-card">
                    <div className="user-header">
                        <div className="header-left">
                            <Link to="/admin" className="back-link" title="Back to Admin Panel">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                                </svg>
                            </Link>
                            <h1>User Maintenance</h1>
                        </div>
                    </div>

                    <div className="user-controls">
                        <input
                            type="text"
                            placeholder="Search users by name, email..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>

                    {loading ? (
                        <LoadingSpinner message="Loading users..." />
                    ) : error ? (
                        <ErrorDisplay error={error} onRetry={fetchUsers} />
                    ) : (
                        <div className="user-list">
                            {users.length === 0 ? (
                                <div className="empty-state">No users found.</div>
                            ) : (
                                <table className="user-table">
                                    <thead>
                                        <tr>
                                            <th onClick={() => handleSort('display_name')} className="sortable">
                                                Name {sortConfig.key === 'display_name' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                                            </th>
                                            <th onClick={() => handleSort('email')} className="sortable">
                                                Email {sortConfig.key === 'email' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                                            </th>
                                            <th onClick={() => handleSort('role')} className="sortable">
                                                Role {sortConfig.key === 'role' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                                            </th>
                                            <th onClick={() => handleSort('is_banned')} className="sortable">
                                                Status {sortConfig.key === 'is_banned' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                                            </th>
                                            <th className="actions-col">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {sortedUsers.map(user => (
                                            <tr key={user.user_id}>
                                                <td>
                                                    <div className="user-name">{user.display_name}</div>
                                                </td>
                                                <td>{user.email}</td>
                                                <td>
                                                    <span className={`role-badge role-${user.role.toLowerCase()}`}>
                                                        {user.role}
                                                    </span>
                                                </td>
                                                <td>
                                                    {user.is_banned ? (
                                                        <span className="status-badge status-banned">BANNED</span>
                                                    ) : (
                                                        <span className="status-badge status-active">Active</span>
                                                    )}
                                                </td>
                                                <td className="actions-col">
                                                    <Button
                                                        variant="secondary"
                                                        size="sm"
                                                        onClick={() => handleEditUser(user)}
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
