import React, { useState } from 'react';
import { deleteAccount } from '../api/users';
import Button from './common/Button';
import './DeleteAccountModal.css';

const DeleteAccountModal = ({ isOpen, onClose, onDeleteSuccess }) => {
    const [isDeleting, setIsDeleting] = useState(false);
    const [error, setError] = useState(null);

    if (!isOpen) return null;

    const handleDelete = async () => {
        setIsDeleting(true);
        setError(null);
        try {
            await deleteAccount();
            if (onDeleteSuccess) onDeleteSuccess();
            onClose();
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to delete account");
            setIsDeleting(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="modal-content delete-account-modal"
                onClick={e => e.stopPropagation()}
            >
                <div className="modal-header">
                    <h2>Delete Account</h2>
                    <button className="close-btn" onClick={onClose} aria-label="Close">×</button>
                </div>

                <div className="modal-body">
                    <p className="modal-description">
                        Are you sure you want to delete your account? This action cannot be undone.
                    </p>
                    <p className="modal-subtext">
                        Your account will be permanently removed. Your edits will be preserved but anonymized (associated with "Deleted User").
                    </p>

                    {error && (
                        <div className="error-banner">
                            {error}
                        </div>
                    )}
                </div>

                <div className="modal-footer">
                    <Button
                        variant="ghost"
                        onClick={onClose}
                        disabled={isDeleting}
                    >
                        Cancel
                    </Button>
                    <Button
                        variant="danger"
                        onClick={handleDelete}
                        disabled={isDeleting}
                    >
                        {isDeleting ? 'Deleting...' : 'Delete Permanently'}
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default DeleteAccountModal;
