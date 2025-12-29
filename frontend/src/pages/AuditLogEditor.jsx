import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { auditLogApi } from '../api/auditLog';
import DiffTable from '../components/audit-log/DiffTable';
import TeamDiff from '../components/audit-log/diffs/TeamDiff';
import EraDiff from '../components/audit-log/diffs/EraDiff';
import SponsorDiff from '../components/audit-log/diffs/SponsorDiff';
import BrandDiff from '../components/audit-log/diffs/BrandDiff';
import SponsorLinkDiff from '../components/audit-log/diffs/SponsorLinkDiff';
import LineageDiff from '../components/audit-log/diffs/LineageDiff';
import { LoadingSpinner } from '../components/Loading';
import { ErrorDisplay } from '../components/ErrorDisplay';
import Button from '../components/common/Button';
import ReviewModal from '../components/moderation/ReviewModal';
import { formatDateTime } from '../utils/dateUtils';
import { getErrorMessage } from '../utils/errors';
import '../components/maintenance/SponsorEditor.css'; // Shared Editor Styles
import './AuditLogEditor.css'; // Specific overrides

const STATUS_COLORS = {
    PENDING: 'status-pending',
    APPROVED: 'status-approved',
    REJECTED: 'status-rejected',
    REVERTED: 'status-reverted'
};

const DIFF_COMPONENTS = {
    TEAM: TeamDiff,
    'TEAM_NODE': TeamDiff,
    'team_node': TeamDiff,

    ERA: EraDiff,
    'TEAM_ERA': EraDiff,
    'team_era': EraDiff,

    SPONSOR: SponsorDiff,
    'SPONSOR_MASTER': SponsorDiff,
    'sponsor_master': SponsorDiff,

    BRAND: BrandDiff,
    'SPONSOR_BRAND': BrandDiff,
    'sponsor_brand': BrandDiff,

    SPONSOR_LINK: SponsorLinkDiff,
    'team_sponsor_link': SponsorLinkDiff,

    LINEAGE: LineageDiff,
    'LINEAGE_EVENT': LineageDiff,
    'lineage_event': LineageDiff
};

export default function AuditLogEditor() {
    const { editId } = useParams();
    const navigate = useNavigate();
    const [edit, setEdit] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState(false);
    const [showReviewModal, setShowReviewModal] = useState(false);

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
            alert('Failed to revert edit: ' + getErrorMessage(err));
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
            alert('Failed to re-apply edit: ' + getErrorMessage(err));
        } finally {
            setActionLoading(false);
        }
    };

    const handleReview = async (editId, approved, notes) => {
        setActionLoading(true);
        try {
            await auditLogApi.review(editId, { approved, notes });
            await loadEdit(); // Reload to see new status
            setShowReviewModal(false);
        } catch (err) {
            console.error('Failed to review edit:', err);
            setError(getErrorMessage(err));
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) return (
        <div className="maintenance-page-container centered-editor-container">
            <LoadingSpinner />
        </div>
    );

    // Normalize entity type for mapping
    const normalizedType = edit?.entity_type;
    // Helper to get the correct diff component
    const DiffComponent = edit ? (DIFF_COMPONENTS[normalizedType] || DiffTable) : DiffTable;

    return (
        <div className="maintenance-page-container audit-log-editor-page">
            <div className="centered-editor-container">
                {/* Header */}
                <div className="editor-header">
                    <div className="header-left">
                        <Button variant="ghost" className="back-btn" onClick={() => navigate('/audit-log')} title="Back to List">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                            </svg>
                        </Button>
                        <h2>Edit Audit Log</h2>
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
                    <div style={{ padding: '2rem' }}>
                        <ErrorDisplay error={error} />
                    </div>
                ) : (
                    edit && (
                        <div className="editor-split-view">
                            {/* LEFT: Metadata */}
                            <div className="editor-column details-column">
                                <div className="column-header">
                                    <h3>Audit Metadata</h3>
                                </div>

                                <div className="audit-metadata-display">
                                    <div className="metadata-section">
                                        <div className="metadata-row">
                                            <label>Entity</label>
                                            <div className="metadata-value">
                                                <span className="entity-type-badge">{edit.entity_type}</span>
                                                <span className="entity-name-highlight">{edit.entity_name}</span>
                                            </div>
                                        </div>

                                        <div className="metadata-row">
                                            <label>Action</label>
                                            <div className="metadata-value">{edit.action}</div>
                                        </div>
                                    </div>

                                    <div className="metadata-divider"></div>

                                    <div className="metadata-section">
                                        <div className="metadata-row">
                                            <label>Submitted</label>
                                            <div className="metadata-value">
                                                <div>{formatDateTime(edit.submitted_at)}</div>
                                                <div className="sub-text">by {edit.submitted_by?.display_name || 'Unknown'}</div>
                                                {(edit.submitted_by?.email) && <div className="sub-text email">({edit.submitted_by.email})</div>}
                                            </div>
                                        </div>
                                    </div>

                                    {(edit.review_notes || edit.summary) && (
                                        <>
                                            <div className="metadata-divider"></div>
                                            <div className="metadata-section">
                                                <label>Notes / Summary</label>
                                                <div className="metadata-value notes-block">
                                                    {edit.review_notes || edit.summary}
                                                </div>
                                            </div>
                                        </>
                                    )}

                                    {edit.reviewed_by && (
                                        <>
                                            <div className="metadata-divider"></div>
                                            <div className="metadata-section">
                                                <div className="metadata-row">
                                                    <label>Reviewed</label>
                                                    <div className="metadata-value">
                                                        <div>{formatDateTime(edit.reviewed_at)}</div>
                                                        <div className="sub-text">by {edit.reviewed_by?.display_name || '-'}</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>

                            {/* RIGHT: Changes / Diff */}
                            <div className="editor-column brands-column" style={{ background: 'var(--color-bg-secondary)' }}>
                                <div className="column-header">
                                    <h3>Proposed Changes</h3>
                                </div>
                                <div className="diff-wrapper" style={{ marginTop: '1rem' }}>
                                    <DiffComponent
                                        before={edit.snapshot_before}
                                        after={edit.snapshot_after}
                                    />
                                </div>
                            </div>
                        </div>
                    )
                )}

                {/* Footer */}
                <div className="editor-footer">
                    <div className="footer-actions-left">
                        {/* Revert Action */}
                        {edit && edit.can_revert && (
                            <Button
                                variant="danger"
                                className="footer-btn"
                                onClick={handleRevert}
                                disabled={actionLoading}
                                style={{ borderColor: '#991b1b', color: '#fca5a5' }}
                            >
                                {actionLoading ? 'Reverting...' : 'Revert Edit'}
                            </Button>
                        )}

                        {/* Reapply logic */}
                        {edit && (edit.status === 'REVERTED' || edit.status === 'REJECTED') && (
                            <Button
                                variant="secondary"
                                className="footer-btn"
                                onClick={handleReapply}
                                disabled={actionLoading}
                            >
                                {actionLoading ? 'Re-applying...' : 'Re-apply Edit'}
                            </Button>
                        )}
                    </div>

                    <div className="footer-actions-right">
                        <Button
                            variant="secondary"
                            className="footer-btn"
                            onClick={() => navigate('/audit-log')}
                            disabled={actionLoading}
                        >
                            Close
                        </Button>

                        {/* Moderation Actions */}
                        {edit && (edit.can_approve || edit.can_reject) && (
                            <Button
                                variant="primary"
                                onClick={() => setShowReviewModal(true)}
                                className="footer-btn save"
                                disabled={actionLoading}
                            >
                                Review Edit
                            </Button>
                        )}
                    </div>
                </div>

                {showReviewModal && (
                    <ReviewModal
                        edit={edit}
                        onClose={() => setShowReviewModal(false)}
                        onReview={handleReview}
                    />
                )}
            </div>
        </div>
    );
}
