import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { auditLogApi } from '../api/auditLog';
import { useAuth } from './AuthContext';

const AuditLogContext = createContext(null);

/** Polling interval for pending edits count (60 seconds) */
const POLL_INTERVAL_MS = 60000;

export function useAuditLog() {
    return useContext(AuditLogContext);
}

export function AuditLogProvider({ children }) {
    const { user, isAdmin, isModerator } = useAuth();
    const [pendingCount, setPendingCount] = useState(0);

    // Safely check if user has moderator/admin permissions
    const canViewAuditLog = user && (
        (typeof isAdmin === 'function' && isAdmin()) ||
        (typeof isModerator === 'function' && isModerator())
    );

    const fetchPendingCount = useCallback(async () => {
        try {
            const res = await auditLogApi.getPendingCount();
            setPendingCount(res.data.count);
        } catch (err) {
            console.error('Failed to fetch pending count:', err);
        }
    }, []);

    useEffect(() => {
        if (!canViewAuditLog) {
            setPendingCount(0);
            return;
        }

        // Initial fetch
        fetchPendingCount();

        // Poll periodically
        const interval = setInterval(fetchPendingCount, POLL_INTERVAL_MS);

        return () => clearInterval(interval);
    }, [canViewAuditLog, fetchPendingCount]);

    const value = {
        pendingCount,
        refreshPendingCount: fetchPendingCount
    };

    return (
        <AuditLogContext.Provider value={value}>
            {children}
        </AuditLogContext.Provider>
    );
}
