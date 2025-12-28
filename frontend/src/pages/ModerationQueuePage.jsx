import { useState, useEffect, useRef } from 'react';
import { moderationApi } from '../api/moderation';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { formatDate, formatDateTime } from '../utils/dateUtils';
import './ModerationQueuePage.css';

import CenteredPageLayout from '../components/layout/CenteredPageLayout';
import Card from '../components/common/Card';
import Button from '../components/common/Button';

function LoadingSpinner() {
  return <div className="loading-spinner">Loading...</div>;
}

function Toast({ message, onClose }) {
  useEffect(() => {
    if (message) {
      const timer = setTimeout(onClose, 3000);
      return () => clearTimeout(timer);
    }
  }, [message, onClose]);
  if (!message) return null;
  return (
    <div className="toast">
      {message}
      <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close" style={{ padding: '0 8px' }}>×</Button>
    </div>
  );
}
export default function ModerationQueuePage() {
  const { isAdmin } = useAuth();
  const navigate = useNavigate();
  const [edits, setEdits] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [selectedEdit, setSelectedEdit] = useState(null);
  const [toast, setToast] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAdmin()) {
      navigate('/');
      return;
    }
    loadData();
  }, [filter]);

  const loadData = async () => {
    setLoading(true);
    setError("");
    try {
      const [editsResponse, statsResponse] = await Promise.all([
        moderationApi.getPendingEdits({ edit_type: filter === 'ALL' ? null : filter }),
        moderationApi.getStats()
      ]);
      setEdits(editsResponse.data);
      setStats(statsResponse.data);
    } catch (error) {
      setError('Failed to load moderation data: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (editId, approved, notes) => {
    setError("");
    try {
      await moderationApi.reviewEdit(editId, { approved, notes });
      setEdits(prev => prev.filter(e => e.edit_id !== editId));
      setSelectedEdit(null);
      const statsResponse = await moderationApi.getStats();
      setStats(statsResponse.data);
      setToast(approved ? 'Edit approved!' : 'Edit rejected!');
    } catch (error) {
      setError('Failed to review edit: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <CenteredPageLayout>
      <Card title="Moderation Queue">
        <div className="moderation-page-content">
          <Toast message={toast} onClose={() => setToast("")} />
          {loading && <LoadingSpinner />}
          {error && <div className="error-display">{error}</div>}

          {stats && (
            <div className="stats-bar">
              <div className="stat">
                <span className="stat-label">Pending</span>
                <span className="stat-value">{stats.pending_count}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Approved Today</span>
                <span className="stat-value approved">{stats.approved_today}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Rejected Today</span>
                <span className="stat-value rejected">{stats.rejected_today}</span>
              </div>
            </div>
          )}

          <div className="filter-bar">
            <Button variant="secondary" active={filter === 'ALL'} onClick={() => setFilter('ALL')}>
              All ({stats?.pending_count || 0})
            </Button>
            <Button variant="secondary" active={filter === 'METADATA'} onClick={() => setFilter('METADATA')}>
              Metadata ({stats?.pending_by_type?.METADATA || 0})
            </Button>
            <Button variant="secondary" active={filter === 'SPONSOR'} onClick={() => setFilter('SPONSOR')}>
              Sponsors ({stats?.pending_by_type?.SPONSOR || 0})
            </Button>
            <Button variant="secondary" active={filter === 'MERGE'} onClick={() => setFilter('MERGE')}>
              Lineage ({((stats?.pending_by_type?.MERGE || 0) + (stats?.pending_by_type?.SPLIT || 0))})
            </Button>
          </div>
          <div className="edits-list">
            {edits.length === 0 && !loading ? (
              <div className="empty-state">
                <p>🎉 No pending edits! Queue is clear.</p>
              </div>
            ) : (
              edits.map(edit => (
                <div key={edit.edit_id} className="edit-card" onClick={() => setSelectedEdit(edit)} tabIndex={0} role="button" aria-pressed="false" onKeyDown={e => { if (e.key === 'Enter') { setSelectedEdit(edit); } }}>
                  <div className="edit-header">
                    <span className="edit-type">{edit.edit_type}</span>
                    <span className="edit-date">{formatDate(edit.created_at)}</span>
                  </div>
                  <div className="edit-user">By: {edit.user_display_name || edit.user_email}</div>
                  <div className="edit-target">
                    {edit.target_info.team_name && (
                      <span>{edit.target_info.team_name} ({edit.target_info.year})</span>
                    )}
                  </div>
                  <div className="edit-reason">
                    {edit.reason.substring(0, 100)}
                    {edit.reason.length > 100 && '...'}
                  </div>
                </div>
              ))
            )}
          </div>
          {selectedEdit && (
            <EditReviewModal edit={selectedEdit} onClose={() => setSelectedEdit(null)} onReview={handleReview} />
          )}
        </div>
      </Card>
    </CenteredPageLayout>
  );
}

function EditReviewModal({ edit, onClose, onReview }) {
  const [notes, setNotes] = useState('');
  const [reviewing, setReviewing] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    if (modalRef.current) {
      modalRef.current.focus();
    }
  }, []);

  const handleApprove = async () => {
    setReviewing(true);
    await onReview(edit.edit_id, true, notes);
    setReviewing(false);
  };

  const handleReject = async () => {
    if (!notes) {
      setNotes("");
      return;
    }
    setReviewing(true);
    await onReview(edit.edit_id, false, notes);
    setReviewing(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content review-modal"
        onClick={e => e.stopPropagation()}
        tabIndex={-1}
        ref={modalRef}
        onKeyDown={handleKeyDown}
        aria-modal="true"
        role="dialog"
      >
        <div className="modal-header">
          <h2>Review Edit</h2>
          <Button variant="ghost" onClick={onClose} aria-label="Close">×</Button>
        </div>
        <div className="modal-body">
          <div className="review-section">
            <h3>Edit Type</h3>
            <p className="edit-type-badge">{edit.edit_type}</p>
          </div>
          <div className="review-section">
            <h3>Submitted By</h3>
            <p>{edit.user_display_name || edit.user_email}</p>
            <p className="date">{formatDateTime(edit.created_at)}</p>
          </div>
          <div className="review-section">
            <h3>Target</h3>
            <pre>{JSON.stringify(edit.target_info, null, 2)}</pre>
          </div>
          <div className="review-section">
            <h3>Changes</h3>
            <pre>{JSON.stringify(edit.changes, null, 2)}</pre>
          </div>
          <div className="review-section">
            <h3>Reason</h3>
            <p>{edit.reason}</p>
          </div>
          <div className="review-section">
            <h3>Review Notes (Optional for approval, required for rejection)</h3>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Add notes about your decision..."
              rows={4}
              aria-label="Review notes"
            />
          </div>
        </div>
        <div className="modal-footer">
          <Button variant="danger" onClick={handleReject} disabled={reviewing || !notes} className="reject-button">Reject</Button>
          <Button variant="success" onClick={handleApprove} disabled={reviewing} className="approve-button">Approve & Apply</Button>
        </div>
      </div>
    </div>
  );
}
