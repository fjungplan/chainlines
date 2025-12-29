import React, { useState, useRef, useEffect } from 'react';
import Button from '../common/Button';
import { formatDateTime } from '../../utils/dateUtils';
import './ReviewModal.css';

/**
 * Modal for reviewing pending edits in the audit log
 * @param {Object} props
 * @param {Object} props.edit - Edit object to review
 * @param {string} props.edit.edit_id - Unique identifier for the edit
 * @param {string} [props.edit.entity_type] - Type of entity being edited (new schema)
 * @param {string} [props.edit.edit_type] - Type of edit (legacy schema, fallback)
 * @param {Object} [props.edit.submitted_by] - Submitter information (new schema)
 * @param {string} [props.edit.submitted_by.display_name] - Display name of submitter
 * @param {string} [props.edit.submitted_by.email] - Email of submitter
 * @param {string} [props.edit.user_display_name] - Legacy field for user display name
 * @param {string} [props.edit.submitted_at] - Submission timestamp (ISO string, new schema)
 * @param {string} [props.edit.created_at] - Creation timestamp (legacy schema, fallback)
 * @param {Object} [props.edit.snapshot_after] - Snapshot of data after the edit
 * @param {Function} props.onClose - Callback to close the modal
 * @param {Function} props.onReview - Review handler: (editId: string, approved: boolean, notes: string) => Promise<void>
 */
export default function ReviewModal({ edit, onClose, onReview }) {
    const [notes, setNotes] = useState('');
    const [reviewing, setReviewing] = useState(false);
    const [validationError, setValidationError] = useState('');
    const modalRef = useRef(null);

    useEffect(() => {
        if (modalRef.current) {
            modalRef.current.focus();
        }
    }, []);

    const handleApprove = async () => {
        setValidationError('');
        setReviewing(true);
        try {
            await onReview(edit.edit_id, true, notes);
            // Parent component handles modal closing on success
        } catch (err) {
            setReviewing(false);
            throw err; // Let parent handle error display
        }
    };

    const handleReject = async () => {
        if (!notes.trim()) {
            setValidationError('Rejection notes are required to explain your decision');
            return;
        }
        setValidationError('');
        setReviewing(true);
        try {
            await onReview(edit.edit_id, false, notes);
            // Parent component handles modal closing on success
        } catch (err) {
            setReviewing(false);
            throw err; // Let parent handle error display
        }
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
                        <p className="edit-type-badge">{edit.entity_type || edit.edit_type}</p>
                    </div>
                    <div className="review-section">
                        <h3>Submitted By</h3>
                        <p>{edit.submitted_by?.display_name || edit.submitted_by?.email || edit.user_display_name}</p>
                        <p className="date">{formatDateTime(edit.submitted_at || edit.created_at)}</p>
                    </div>

                    {/* Changes Section - Adapted for Audit Log Format */}
                    {edit.snapshot_after && (
                        <div className="review-section">
                            <h3>Changes</h3>
                            <pre>{JSON.stringify(edit.snapshot_after, null, 2)}</pre>
                        </div>
                    )}

                    <div className="review-section">
                        <h3>Review Notes (Required for rejection)</h3>
                        <textarea
                            value={notes}
                            onChange={e => {
                                setNotes(e.target.value);
                                if (validationError) setValidationError('');
                            }}
                            placeholder="Add notes about your decision..."
                            rows={4}
                            aria-label="Review notes"
                            className={validationError ? 'validation-error' : ''}
                        />
                        {validationError && (
                            <div className="error-message" role="alert">
                                {validationError}
                            </div>
                        )}
                    </div>
                </div>
                <div className="modal-footer">
                    <Button
                        variant="danger"
                        onClick={handleReject}
                        disabled={reviewing || !notes}
                        className="reject-button"
                    >
                        Reject
                    </Button>
                    <Button
                        variant="success"
                        onClick={handleApprove}
                        disabled={reviewing}
                        className="approve-button"
                    >
                        Approve & Apply
                    </Button>
                </div>
            </div>
        </div>
    );
}
