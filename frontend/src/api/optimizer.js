import apiClient from './client';

export const optimizerApi = {
    /**
     * Get list of all cached families and their metadata.
     */
    getFamilies: async () => {
        const response = await apiClient.get('/api/v1/admin/optimizer/families');
        return response.data;
    },

    /**
     * Trigger background optimization for specific families.
     * @param {string[]} familyHashes
     */
    triggerOptimization: async (familyHashes) => {
        const response = await apiClient.post('/api/v1/admin/optimizer/optimize', {
            family_hashes: familyHashes
        });
        return response.data;
    },

    /**
     * Get current optimizer status.
     */
    getStatus: async () => {
        const response = await apiClient.get('/api/v1/admin/optimizer/status');
        return response.data;
    },

    /**
     * Get logs for a specific family.
     * @param {string} familyHash
     */
    getFamilyLogs: async (familyHash) => {
        const response = await apiClient.get(`/api/v1/admin/optimizer/families/${familyHash}/logs`);
        return response.data;
    },

    /**
     * Trigger background scan for new families.
     */
    discoverFamilies: async () => {
        const response = await apiClient.post('/api/v1/admin/optimizer/discover');
        return response.data;
    }
};
