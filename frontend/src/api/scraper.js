import apiClient from './client';

export const scraperApi = {
    // Checkpoint & Status
    getCheckpoint: () => apiClient.get('/admin/scraper/checkpoint'),

    // Controls
    startScraper: (data) => apiClient.post('/admin/scraper/start', data),

    // History & Logs
    getRuns: (skip = 0, limit = 20) => apiClient.get(`/admin/scraper/runs?skip=${skip}&limit=${limit}`),
    getRunLogs: (runId) => apiClient.get(`/admin/scraper/runs/${runId}/logs`),
};
