import { apiClient as api } from './client';

export const lineageApi = {
    listEvents: async (params) => {
        const response = await api.get('/api/v1/lineage', { params });
        return response.data;
    },

    // Future: edit/delete if needed
    // deleteEvent: async (id) => { ... }
};
