import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { updateUser } from '../../api/users';
import { formatDate, formatDateTime } from '../../utils/dateUtils';
import Button from '../common/Button';
import './SponsorEditor.css'; // Reuse SponsorEditor styles like TeamEraEditor does
import './UserEditor.css';

export default function UserEditor({ user, onClose, onSuccess }) {
    const { isAdmin, user: currentUser } = useAuth();

    // Prevent admins from accidentally banning/demoting themselves
    const isSelf = currentUser && user && currentUser.user_id === user.user_id;

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const [formData, setFormData] = useState({
        role: user?.role || 'EDITOR',
        is_banned: user?.is_banned || false,
        banned_reason: user?.banned_reason || ''
    });

    // Update form when user prop changes
    useEffect(() => {
        if (user) {
            setFormData({
                role: user.role,
                is_banned: user.is_banned || false,
                banned_reason: user.banned_reason || ''
            });
        }
    }, [user]);

    if (!user) return <div className="team-inner-container">No user selected</div>;

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSave = async (shouldClose) => {
        setSubmitting(true);
        setError(null);
        try {
            await updateUser(user.user_id, formData);
            if (shouldClose && onSuccess) {
                onSuccess();
            } else {
                setSubmitting(false);
            }
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || "Failed to update user");
            setSubmitting(false);
        }
    };

    return (
        <div className="team-inner-container centered-editor-container">
            <div className="editor-header">
                <div className="header-left">
                    <Button variant="ghost" className="back-btn" onClick={onClose} title="Back to Users">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                        </svg>
                    </Button>
                    <h2>Edit User: {user.display_name}</h2>
                </div>
            </div>

            <div className="editor-split-view">
                {/* FORM */}
                <div className="editor-column details-column">
                    <div className="column-header">
                        <h3>User Properties</h3>
                        <label className={`status-toggle ${isSelf ? 'disabled' : ''}`} title={isSelf ? "Cannot ban yourself" : ""}>
                            <input
                                type="checkbox"
                                checked={formData.is_banned}
                                onChange={e => handleChange('is_banned', e.target.checked)}
                                disabled={isSelf}
                            />
                            <span>Banned</span>
                        </label>
                    </div>

                    {error && <div className="error-banner">{error}</div>}

                    <form onSubmit={(e) => { e.preventDefault(); }}>
                        {/* Read-only Info */}
                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Display Name</label>
                                <input type="text" value={user.display_name} readOnly disabled />
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Email</label>
                                <input type="text" value={user.email} readOnly disabled />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Google ID</label>
                                <input type="text" value={user.google_id || '-'} readOnly disabled />
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Member Since</label>
                                <input type="text" value={formatDate(user.created_at)} readOnly disabled />
                            </div>
                        </div>

                        {/* Editable Fields */}
                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Role * {isSelf && <span style={{ color: '#666', fontSize: '0.8rem' }}>(cannot change own role)</span>}</label>
                                <select
                                    value={formData.role}
                                    onChange={e => handleChange('role', e.target.value)}
                                    disabled={isSelf}
                                >
                                    <option value="EDITOR">Editor</option>
                                    <option value="TRUSTED_EDITOR">Trusted Editor</option>
                                    <option value="MODERATOR">Moderator</option>
                                    <option value="ADMIN">Admin</option>
                                </select>
                            </div>
                        </div>



                        {formData.is_banned && (
                            <div className="form-row">
                                <div className="form-group full-width">
                                    <label>Ban Reason</label>
                                    <textarea
                                        value={formData.banned_reason}
                                        onChange={e => handleChange('banned_reason', e.target.value)}
                                        placeholder="Reason for ban..."
                                        rows={3}
                                        style={{ width: '100%', resize: 'vertical' }}
                                    />
                                </div>
                            </div>
                        )}
                    </form>
                </div>

                {/* RIGHT: User Stats */}
                <div className="editor-column brands-column">
                    <div className="column-header">
                        <h3>User Statistics</h3>
                    </div>
                    <div className="stats-list">
                        <div className="stat-item">
                            <span className="stat-label">Approved Edits</span>
                            <span className="stat-value">{user.approved_edits_count || 0}</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-label">Last Login</span>
                            <span className="stat-value">
                                {formatDateTime(user.last_login_at, 'Never')}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* FOOTER */}
            <div className="editor-footer">
                <div className="footer-actions-left">
                    <Button
                        variant="secondary"
                        className="footer-btn"
                        onClick={onClose}
                        disabled={submitting}
                    >
                        Back
                    </Button>
                </div>
                <div className="footer-actions-right">
                    <Button
                        variant="primary"
                        className="footer-btn save"
                        onClick={() => handleSave(false)}
                        disabled={submitting}
                    >
                        Save
                    </Button>
                    <Button
                        variant="primary"
                        className="footer-btn save-close"
                        onClick={() => handleSave(true)}
                        disabled={submitting}
                    >
                        Save & Close
                    </Button>
                </div>
            </div>
        </div>
    );
}
