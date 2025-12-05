import apiClient from './client';

export const moderationApi = {
  getPendingEdits: (params) =>
    apiClient.get('/api/v1/moderation/pending', { params }),

  reviewEdit: (editId, data) =>
    apiClient.post(`/api/v1/moderation/review/${editId}`, data),

  getStats: () =>
    apiClient.get('/api/v1/moderation/stats'),
};
