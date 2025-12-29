/**
 * Audit Log API client
 *
 * Provides functions to interact with the audit log endpoints
 * for viewing edit history and performing moderation actions.
 */
import apiClient from './client';

export const auditLogApi = {
    /**
     * Get list of edits with optional filters
     * @param {Object} params - Query parameters
     * @param {string[]} params.status - Filter by status(es): PENDING, APPROVED, REJECTED, REVERTED
     * @param {string} params.entity_type - Filter by entity type
     * @param {string} params.user_id - Filter by submitter user ID
     * @param {string} params.start_date - Filter by start date (ISO 8601)
     * @param {string} params.end_date - Filter by end date (ISO 8601)
     * @param {number} params.skip - Pagination offset
     * @param {number} params.limit - Pagination limit
     */
    getList: (params = {}) =>
        apiClient.get('/api/v1/audit-log', { params }),

    /**
     * Get full details of a single edit
     * @param {string} editId - UUID of the edit
     */
    getDetail: (editId) =>
        apiClient.get(`/api/v1/audit-log/${editId}`),

    /**
     * Get count of pending edits (for notification badge)
     */
    getPendingCount: () =>
        apiClient.get('/api/v1/audit-log/pending-count'),

    /**
     * Revert an approved edit
     * @param {string} editId - UUID of the edit to revert
     * @param {Object} data - Request body with optional notes
     */
    revert: (editId, data = {}) =>
        apiClient.post(`/api/v1/audit-log/${editId}/revert`, data),

    /**
     * Re-apply a reverted or rejected edit
     * @param {string} editId - UUID of the edit to re-apply
     * @param {Object} data - Request body with optional notes
     */
    reapply: (editId, data = {}) =>
        apiClient.post(`/api/v1/audit-log/${editId}/reapply`, data),
};

export default auditLogApi;
