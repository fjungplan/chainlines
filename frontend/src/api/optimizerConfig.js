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
    }
};
