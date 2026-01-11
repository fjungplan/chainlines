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

const formatEntityType = (type) => {
    if (!type) return '-';
    // Map of raw types to friendly names
    const typeMap = {
        'team_node': 'Team',
        'sponsor_master': 'Sponsor',
        'team_era': 'Team Era',
        'linkage_event': 'Lineage Event',
        'team_sponsor_link': 'Sponsor Link',
        'brand': 'Brand'
    };
    return typeMap[type] || type.replace(/_/g, ' '); // Fallback: replace underscores with spaces
};

export default function AuditLogEditor({ backPath = '/audit-log', apiMethod = null }) {
    const { editId } = useParams();
    const navigate = useNavigate();

    // Default to auditLogApi.getDetail if no apiMethod provided
    const getDetailFn = apiMethod || auditLogApi.getDetail;
    const [edit, setEdit] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [actionLoading, setActionLoading] = useState(false);

    // Modal Configuration
    const [modalConfig, setModalConfig] = useState({
        isOpen: false,
        title: '',
        action: '',
        variant: 'danger',
        onConfirm: null
    });

    const loadEdit = async () => {
        try {
            setLoading(true);
            const res = await getDetailFn(editId);
            setEdit(res.data);
            setError(null);
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadEdit();
    }, [editId]);

    const closeModal = () => {
        setModalConfig(prev => ({ ...prev, isOpen: false }));
    };

    const handleApprove = async () => {
        setModalConfig({
            isOpen: true,
            title: 'Approve Edit',
            action: 'Approve',
            variant: 'success', // Green button
            isReasonRequired: false,
            onConfirm: async (notes) => {
                await auditLogApi.review(editId, { approved: true, notes: notes || 'Approved via UI' });
                await loadEdit();
                setModalConfig(prev => ({ ...prev, isOpen: false }));
            }
        });
    };

    const handleRejectClick = () => {
        setModalConfig({
            isOpen: true,
            title: 'Reject Edit',
            action: 'Reject',
            variant: 'danger',
            onConfirm: async (notes) => {
                await auditLogApi.review(editId, { approved: false, notes });
                await loadEdit();
                setModalConfig(prev => ({ ...prev, isOpen: false }));
            }
        });
    };

    const handleRevertClick = () => {
        setModalConfig({
            isOpen: true,
            title: 'Revert Edit',
            action: 'Revert',
            variant: 'danger',
            onConfirm: async (notes) => {
                await auditLogApi.revert(editId, { notes });
                await loadEdit();
                setModalConfig(prev => ({ ...prev, isOpen: false }));
            }
        });
    };

    const handleReapplyClick = () => {
        setModalConfig({
            isOpen: true,
            title: 'Re-apply Edit',
            action: 'Re-apply',
            variant: 'primary',
            onConfirm: async (notes) => {
                await auditLogApi.reapply(editId, { notes });
                await loadEdit();
                setModalConfig(prev => ({ ...prev, isOpen: false }));
            }
        });
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
                        <Button variant="ghost" className="back-btn" onClick={() => navigate(backPath)} title="Back to List">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M20 11H7.83L13.42 5.41L12 4L4 12L12 20L13.41 18.59L7.83 13H20V11Z" fill="currentColor" />
                            </svg>
                        </Button>
                        <h2>View Audit Log</h2>
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
                                                <span className="entity-type-badge">{formatEntityType(edit.entity_type)}</span>
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
                                onClick={handleRevertClick}
                                disabled={actionLoading}
                                style={{ borderColor: '#991b1b', color: '#fca5a5' }}
                            >
                                Revert Edit
                            </Button>
                        )}

                        {/* Reapply logic */}
                        {edit && (edit.status === 'REVERTED' || edit.status === 'REJECTED') && (
                            <Button
                                variant="secondary"
                                className="footer-btn"
                                onClick={handleReapplyClick}
                                disabled={actionLoading}
                            >
                                Re-apply Edit
                            </Button>
                        )}
                    </div>

                    <div className="footer-actions-right">
                        <Button
                            variant="secondary"
                            className="footer-btn"
                            onClick={() => navigate(backPath)}
                            disabled={actionLoading}
                        >
                            Close
                        </Button>

                        {/* Moderation Actions - Split Buttons */}
                        {edit && edit.can_reject && (
                            <Button
                                variant="danger"
                                onClick={handleRejectClick}
                                className="footer-btn"
                                disabled={actionLoading}
                            >
                                Reject
                            </Button>
                        )}

                        {edit && edit.can_approve && (
                            <Button
                                variant="success"
                                onClick={handleApprove}
                                className="footer-btn save"
                                disabled={actionLoading}
                            >
                                Approve
                            </Button>
                        )}
                    </div>
                </div>

                {modalConfig.isOpen && (
                    <ReviewModal
                        isOpen={modalConfig.isOpen}
                        title={modalConfig.title}
                        action={modalConfig.action}
                        variant={modalConfig.variant}
                        isReasonRequired={modalConfig.isReasonRequired}
                        onClose={closeModal}
                        onConfirm={modalConfig.onConfirm}
                    />
                )}
            </div>
        </div>
    );
}
