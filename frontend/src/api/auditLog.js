/**
 * Audit Log API client
 *
 * Provides functions to interact with the audit log endpoints
 * for viewing edit history and performing moderation actions.
 */
import apiClient from './client';

export const auditLogApi = {
    /**
     * Get list of audit log entries.
     * @param {Object} params - Query parameters.
     * @param {number} params.skip - Pagination skip.
     * @param {number} params.limit - Pagination limit.
     * @param {string[]} [params.status] - Filter by status.
     * @param {string} [params.entity_type] - Filter by entity type.
     * @param {string} [params.search] - Search query.
     * @returns {Promise<Object>} Object containing items and total count.
     */
    getList: (params) => apiClient.get('/api/v1/audit-log', { params }),

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

    // Moderation action
    review: (editId, data) =>
        apiClient.post(`/api/v1/moderation/review/${editId}`, data),
};

export default auditLogApi;
