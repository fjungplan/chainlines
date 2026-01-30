import axios from 'axios';

const API_BASE_URL = '/api/admin/optimizer';

export const optimizerConfigApi = {
    /**
     * Get current optimizer configuration
     */
    async getConfig() {
        const response = await axios.get(`${API_BASE_URL}/config`);
        return response.data;
    },

    /**
     * Update optimizer configuration
     * @param {Object} config - Full configuration object
     */
    async updateConfig(config) {
        const response = await axios.put(`${API_BASE_URL}/config`, config);
        return response.data;
    }
};
