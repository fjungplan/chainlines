import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { getUsers } from '../../api/users';
import { LoadingSpinner } from '../../components/Loading';
import { ErrorDisplay } from '../../components/ErrorDisplay';
import Button from '../../components/common/Button';
import UserEditor from '../../components/maintenance/UserEditor';
import './UserMaintenancePage.css'; // Will create

import { useDebounce } from '../../hooks/useDebounce';

export default function UserMaintenancePage() {
    const { isAdmin } = useAuth();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [search, setSearch] = useState('');
    const debouncedSearch = useDebounce(search, 500);
    const [editingUser, setEditingUser] = useState(null);

    const fetchUsers = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getUsers({ search: debouncedSearch, limit: 50 });
            setUsers(data.items);
        } catch (err) {
            setError("Failed to load users.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isAdmin()) {
            fetchUsers();
        }
    }, [debouncedSearch]);

    if (!isAdmin()) return <div>Access Denied</div>;

    const handleEditSuccess = () => {
        setEditingUser(null);
        fetchUsers();
    };

    return (
        <div className="maintenance-page-container">
            <div className="maintenance-content-card">
                <h1>User Maintenance</h1>

                <div className="controls">
                    <input
                        type="text"
                        placeholder="Search users..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>

                {loading ? (
                    <LoadingSpinner message="Loading users..." />
                ) : error ? (
                    <ErrorDisplay error={error} onRetry={fetchUsers} />
                ) : (
                    <table className="user-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.user_id}>
                                    <td>{u.display_name}</td>
                                    <td>{u.email}</td>
                                    <td>{u.role}</td>
                                    <td>{u.is_banned ? <span className="banned-badge">BANNED</span> : 'Active'}</td>
                                    <td>
                                        <Button size="sm" onClick={() => setEditingUser(u)}>Edit</Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {editingUser && (
                <UserEditor
                    user={editingUser}
                    onClose={() => setEditingUser(null)}
                    onSuccess={handleEditSuccess}
                />
            )}
        </div>
    );
}
