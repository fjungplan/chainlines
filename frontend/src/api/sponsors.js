import apiClient from './client';

export const sponsorsApi = {
    // Masters
    getAllMasters: async (skip = 0, limit = 100) => {
        const response = await apiClient.get('/api/v1/sponsors/masters', { params: { skip, limit } });
        return response.data;
    },

    searchMasters: async (query, limit = 20) => {
        const response = await apiClient.get('/api/v1/sponsors/masters', { params: { query, limit } });
        return response.data;
    },

    getMaster: async (masterId) => {
        const response = await apiClient.get(`/api/v1/sponsors/masters/${masterId}`);
        return response.data;
    },

    createMaster: async (data) => {
        const response = await apiClient.post('/api/v1/sponsors/masters', data);
        return response.data;
    },

    updateMaster: async (masterId, data) => {
        const response = await apiClient.put(`/api/v1/sponsors/masters/${masterId}`, data);
        return response.data;
    },

    deleteMaster: async (masterId) => {
        const response = await apiClient.delete(`/api/v1/sponsors/masters/${masterId}`);
        return response.data;
    },

    // Brands
    searchBrands: async (query, limit = 20) => {
        const response = await apiClient.get('/api/v1/sponsors/brands', { params: { query, limit } });
        return response.data;
    },

    addBrand: async (masterId, data) => {
        const response = await apiClient.post(`/api/v1/sponsors/masters/${masterId}/brands`, data);
        return response.data;
    },

    updateBrand: async (brandId, data) => {
        const response = await apiClient.put(`/api/v1/sponsors/brands/${brandId}`, data);
        return response.data;
    },

    deleteBrand: async (brandId) => {
        const response = await apiClient.delete(`/api/v1/sponsors/brands/${brandId}`);
        return response.data;
    },

    // Era Links
    getEraLinks: async (eraId) => {
        const response = await apiClient.get(`/api/v1/sponsors/eras/${eraId}/links`);
        return response.data;
    },

    linkSponsor: async (eraId, data) => {
        const response = await apiClient.post(`/api/v1/sponsors/eras/${eraId}/links`, data);
        return response.data;
    },

    updateLink: async (linkId, data) => {
        const response = await apiClient.put(`/api/v1/sponsors/eras/links/${linkId}`, data);
        return response.data;
    },

    removeLink: async (linkId) => {
        const response = await apiClient.delete(`/api/v1/sponsors/eras/links/${linkId}`);
        return response.data;
    },

    replaceEraLinks: async (eraId, links) => {
        const response = await apiClient.put(`/api/v1/sponsors/eras/${eraId}/links`, links);
        return response.data;
    }
};
