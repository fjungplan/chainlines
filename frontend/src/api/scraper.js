import apiClient from './client';

export const scraperApi = {
    // Checkpoint & Status
    getCheckpoint: async () => {
        const response = await apiClient.get('/api/v1/admin/scraper/checkpoint');
        return response.data;
    },

    // Controls
    startScraper: async (data) => {
        const response = await apiClient.post('/api/v1/admin/scraper/start', data);
        return response.data;
    },
    pauseScraper: async () => {
        const response = await apiClient.post('/api/v1/admin/scraper/pause');
        return response.data;
    },
    resumeScraper: async () => {
        const response = await apiClient.post('/api/v1/admin/scraper/resume');
        return response.data;
    },
    abortScraper: async () => {
        const response = await apiClient.post('/api/v1/admin/scraper/abort');
        return response.data;
    },

    // History & Logs
    getRuns: async (skip = 0, limit = 20) => {
        const response = await apiClient.get(`/api/v1/admin/scraper/runs?skip=${skip}&limit=${limit}`);
        return response.data;
    },
    getRunLogs: async (runId) => {
        const response = await apiClient.get(`/api/v1/admin/scraper/runs/${runId}/logs`);
        return response.data;
    },
};
