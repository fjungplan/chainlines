import { apiClient as api } from './client';

export const lineageApi = {
    listEvents: async (params) => {
        const response = await api.get('/api/v1/lineage', { params: { ...params, _t: Date.now() } });
        return response.data;
    },

    getEvent: async (eventId) => {
        const response = await api.get(`/api/v1/lineage/${eventId}`);
        return response.data;
    },

    createEvent: async (data) => {
        const response = await api.post('/api/v1/edits/lineage', data);
        return response.data;
    },

    updateEvent: async (eventId, data) => {
        const response = await api.put(`/api/v1/edits/lineage/${eventId}`, data);
        return response.data;
    },

    deleteEvent: async (eventId) => {
        const response = await api.delete(`/api/v1/lineage/${eventId}`);
        return response.data;
    }
};
