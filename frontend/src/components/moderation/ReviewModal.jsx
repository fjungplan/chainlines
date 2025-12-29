import React, { useState, useRef, useEffect } from 'react';
import Button from '../common/Button';
import './ReviewModal.css';

/**
 * Generic Modal for confirming actions with a reason/note.
 * Used for Reject, Revert, and Re-apply actions.
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether the modal is open (controlled by parent mounting)
 * @param {string} props.title - Modal title (e.g. "Reject Edit")
 * @param {string} props.action - Action label (e.g. "Reject", "Revert")
 * @param {string} [props.variant] - Button variant ('danger', 'primary', etc.)
 * @param {Function} props.onClose - Callback to close
 * @param {Function} props.onConfirm - Callback with notes: (notes: string) => Promise<void>
 */
export default function ReviewModal({
    title,
    action,
    variant = 'danger',
    onClose,
    onConfirm,
    isReasonRequired = true
}) {
    const [notes, setNotes] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const modalRef = useRef(null);

    useEffect(() => {
        if (modalRef.current) {
            modalRef.current.focus();
        }
    }, []);

    const handleConfirm = async () => {
        if (isReasonRequired && !notes.trim()) {
            setError('Please provide a reason.');
            return;
        }

        setError('');
        setLoading(true);
        try {
            await onConfirm(notes);
            // Parent closes modal
        } catch (err) {
            setLoading(false);
            // Error handling usually in parent, but we reset loading
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Escape') onClose();
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="modal-content review-modal"
                onClick={e => e.stopPropagation()}
                tabIndex={-1}
                ref={modalRef}
                onKeyDown={handleKeyDown}
                role="dialog"
            >
                <div className="modal-header">
                    <h2>{title}</h2>
                    <Button variant="ghost" onClick={onClose} aria-label="Close">×</Button>
                </div>

                <div className="modal-body">
                    <div className="review-section">
                        <label className="reason-label">
                            {isReasonRequired ? 'Reason (Required)' : 'Reason (Optional)'}
                        </label>
                        <textarea
                            value={notes}
                            onChange={e => {
                                setNotes(e.target.value);
                                if (error) setError('');
                            }}
                            placeholder={isReasonRequired
                                ? "Please enter a reason for this action..."
                                : "Optional: Enter a reason..."}
                            rows={4}
                            className={error ? 'validation-error' : ''}
                            autoFocus
                        />
                        {error && <div className="error-message">{error}</div>}
                    </div>
                </div>

                <div className="modal-footer">
                    <Button
                        variant="ghost"
                        onClick={onClose}
                        disabled={loading}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant={variant}
                        onClick={handleConfirm}
                        disabled={loading || (isReasonRequired && !notes.trim())}
                    >
                        {loading ? 'Processing...' : `Confirm ${action}`}
                    </Button>
                </div>
            </div>
        </div>
    );
}
