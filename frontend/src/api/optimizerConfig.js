import apiClient from './client';

export const optimizerConfigApi = {
    /**
     * Get current optimizer configuration
     */
    async getConfig() {
        const response = await apiClient.get('/api/v1/admin/optimizer/config');
        return response.data;
    },

    /**
     * Update optimizer configuration
     * @param {Object} config - Full configuration object
     */
    async updateConfig(config) {
        const response = await apiClient.put('/api/v1/admin/optimizer/config', config);
        return response.data;
    },

    /**
     * Get all profiles and active ID
     */
    async getProfiles() {
        const response = await apiClient.get('/api/v1/admin/optimizer/profiles');
        return response.data;
    },

    /**
     * Update a specific profile
     */
    async updateProfile(profileId, config) {
        const response = await apiClient.put(`/api/v1/admin/optimizer/profiles/${profileId}`, config);
        return response.data;
    },

    /**
     * Activate a profile
     */
    async activateProfile(profileId) {
        const response = await apiClient.post(`/api/v1/admin/optimizer/profiles/${profileId}/activate`);
        return response.data;
    }
};
