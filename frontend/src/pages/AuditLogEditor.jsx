import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { auditLogApi } from '../api/auditLog';
import DiffTable from '../components/audit-log/DiffTable';
import { LoadingSpinner } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import Button from '../components/common/Button';
import './AuditLogEditor.css';
import { formatDateTime } from '../utils/dateUtils'; // Assuming util exists or helper

const STATUS_COLORS = {
    PENDING: 'status-pending',
    APPROVED: 'status-approved',
    REJECTED: 'status-rejected',
    REVERTED: 'status-reverted'
};

export default function AuditLogEditor() {
    const { editId } = useParams();
    const [edit, setEdit] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        loadEdit();
    }, [editId]);

    const loadEdit = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await auditLogApi.getDetail(editId);
            setEdit(res.data);
        } catch (err) {
            console.error('Failed to load edit:', err);
            setError('Failed to load edit details. It may have been deleted or you do not have permission.');
        } finally {
            setLoading(false);
        }
    };

    const handleRevert = async () => {
        if (!window.confirm('Are you sure you want to revert this edit? This will create a new REVERTED record.')) return;

        setActionLoading(true);
        try {
            await auditLogApi.revert(editId, { notes: 'Reverted via Audit Log UI' });
            await loadEdit(); // Reload to update status
        } catch (err) {
            console.error('Revert failed:', err);
            alert('Failed to revert edit: ' + (err.response?.data?.detail || err.message));
        } finally {
            setActionLoading(false);
        }
    };

    const handleReapply = async () => {
        if (!window.confirm('Are you sure you want to re-apply this edit?')) return;

        setActionLoading(true);
        try {
            await auditLogApi.reapply(editId, { notes: 'Re-applied via Audit Log UI' });
            await loadEdit();
        } catch (err) {
            console.error('Reapply failed:', err);
            alert('Failed to re-apply edit: ' + (err.response?.data?.detail || err.message));
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) return <LoadingSpinner />;

    // Formatting helper if not imported
    const formatDate = (dateStr) => {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleString();
    };

    return (
        <div className="audit-log-editor">
            <div className="maintenance-page-container">
                {/* Header */}
                <div className="maintenance-header">
                    <div className="header-left">
                        <Link to="/audit-log" className="back-link">← Back to List</Link>
                        <h1>Edit Detail</h1>
                    </div>
                    {edit && (
                        <div className="header-right">
                            <span className={`status-badge ${STATUS_COLORS[edit.status] || ''}`}>
                                {edit.status}
                            </span>
                        </div>
                    )}
                </div>

                {error ? (
                    <ErrorDisplay error={error} />
                ) : (
                    edit && (
                        <div className="editor-content">
                            {/* Metadata Card */}
                            <div className="metadata-card">
                                <div className="metadata-grid">
                                    <div className="metadata-item">
                                        <label>Entity Type</label>
                                        <span>{edit.entity_type}</span>
                                    </div>
                                    <div className="metadata-item">
                                        <label>Entity Name</label>
                                        <span className="entity-name-highlight">{edit.entity_name}</span>
                                    </div>
                                    <div className="metadata-item">
                                        <label>Action</label>
                                        <span>{edit.action}</span>
                                    </div>
                                    <div className="metadata-item">
                                        <label>Submitted By</label>
                                        <span>
                                            {edit.submitted_by?.display_name || 'Unknown'}
                                            <span className="metadata-sub"> ({edit.submitted_by?.email})</span>
                                        </span>
                                    </div>
                                    <div className="metadata-item">
                                        <label>Submitted At</label>
                                        <span>{formatDate(edit.submitted_at)}</span>
                                    </div>

                                    {/* Review Info */}
                                    <div className="metadata-item">
                                        <label>Reviewed By</label>
                                        <span>{edit.reviewed_by?.display_name || '-'}</span>
                                    </div>
                                    <div className="metadata-item">
                                        <label>Reviewed At</label>
                                        <span>{formatDate(edit.reviewed_at)}</span>
                                    </div>
                                </div>

                                {(edit.review_notes || edit.summary) && (
                                    <div className="metadata-notes">
                                        <label>Notes / Summary</label>
                                        <div className="notes-content">
                                            {edit.review_notes || edit.summary}
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Diff Section */}
                            <div className="diff-section">
                                <h2>Changes</h2>
                                <DiffTable
                                    before={edit.snapshot_before}
                                    after={edit.snapshot_after}
                                />
                            </div>

                            {/* Actions Footer */}
                            <div className="editor-footer">
                                <div className="footer-actions">
                                    {edit.can_revert && (
                                        <Button
                                            variant="danger"
                                            onClick={handleRevert}
                                            disabled={actionLoading}
                                        >
                                            {actionLoading ? 'Reverting...' : 'Revert Edit'}
                                        </Button>
                                    )}

                                    {/* Reapply logic: If REVERTED or REJECTED? API supports it. */}
                                    {(edit.status === 'REVERTED' || edit.status === 'REJECTED') && (
                                        <Button
                                            variant="secondary"
                                            onClick={handleReapply}
                                            disabled={actionLoading}
                                        >
                                            {actionLoading ? 'Re-applying...' : 'Re-apply Edit'}
                                        </Button>
                                    )}
                                </div>
                            </div>
                        </div>
                    )
                )}
            </div>
        </div>
    );
}
