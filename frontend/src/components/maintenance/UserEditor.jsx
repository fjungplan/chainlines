import React, { useState, useEffect } from 'react';
import Button from '../common/Button';
import { updateUser } from '../../api/users';
import './UserEditor.css'; // We'll create this or use shared styles

export default function UserEditor({ user, onClose, onSuccess }) {
    const [formData, setFormData] = useState({
        role: 'EDITOR',
        is_banned: false,
        banned_reason: ''
    });
    const [error, setError] = useState(null);
    const [saving, setSaving] = useState(false);

    // Load user data
    useEffect(() => {
        if (user) {
            setFormData({
                role: user.role,
                is_banned: user.is_banned,
                banned_reason: user.banned_reason || ''
            });
        }
    }, [user]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);

        try {
            await updateUser(user.user_id, formData);
            onSuccess();
        } catch (err) {
            console.error(err);
            setError("Failed to update user.");
        } finally {
            setSaving(false);
        }
    };

    if (!user) return null;

    return (
        <div className="modal-overlay">
            <div className="modal-content user-editor-modal">
                <h2>Edit User: {user.display_name}</h2>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Role</label>
                        <select name="role" value={formData.role} onChange={handleChange}>
                            <option value="EDITOR">Editor</option>
                            <option value="TRUSTED_EDITOR">Trusted Editor</option>
                            <option value="MODERATOR">Moderator</option>
                            <option value="ADMIN">Admin</option>
                        </select>
                    </div>

                    <div className="form-group checkbox-group">
                        <label>
                            <input
                                type="checkbox"
                                name="is_banned"
                                checked={formData.is_banned}
                                onChange={handleChange}
                            />
                            Banned
                        </label>
                    </div>

                    {formData.is_banned && (
                        <div className="form-group">
                            <label>Ban Reason</label>
                            <textarea
                                name="banned_reason"
                                value={formData.banned_reason}
                                onChange={handleChange}
                                placeholder="Reason for ban..."
                            />
                        </div>
                    )}

                    {error && <div className="error-message">{error}</div>}

                    <div className="modal-actions">
                        <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
                        <Button type="submit" variant="primary" disabled={saving}>
                            {saving ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
