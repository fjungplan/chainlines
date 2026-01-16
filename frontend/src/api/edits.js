import { apiClient as api } from './client';

export const editsApi = {
  // Create Era Edit (for new eras)
  createEraEdit: async (payload) => {
    const response = await api.post('/api/v1/edits/era', payload);
    return response.data;
  },

  // Update Era Edit (for existing eras, supports node_id transfer)
  updateEra: async (eraId, payload) => {
    const response = await api.put(`/api/v1/edits/era/${eraId}`, payload);
    return response.data;
  },

  // Legacy / Generic Metadata edit if needed
  editMetadata: async (payload) => {
    const response = await api.post('/api/v1/edits/metadata', payload);
    return response.data;
  },

  // Create Team Node Request
  createTeamEdit: async (payload) => {
    const response = await api.post('/api/v1/edits/create-team', payload);
    return response.data;
  },

  // Merge/Split
  createMerge: async (payload) => {
    const response = await api.post('/api/v1/edits/merge', payload);
    return response.data;
  },

  createSplit: async (payload) => {
    const response = await api.post('/api/v1/edits/split', payload);
    return response.data;
  },

  // Update Node Request
  updateNode: async (payload) => {
    const response = await api.post('/api/v1/edits/node', payload);
    return response.data;
  },

  // Lineage Events (RBAC)
  createLineageEvent: async (payload) => {
    const response = await api.post('/api/v1/edits/lineage', payload);
    return response.data;
  },

  updateLineageEvent: async (eventId, payload) => {
    const response = await api.put(`/api/v1/edits/lineage/${eventId}`, payload);
    return response.data;
  },

  // Sponsor Master (RBAC)
  createSponsorMaster: async (payload) => {
    const response = await api.post('/api/v1/edits/sponsor-master', payload);
    return response.data;
  },

  updateSponsorMaster: async (masterId, payload) => {
    const response = await api.put(`/api/v1/edits/sponsor-master/${masterId}`, payload);
    return response.data;
  },

  // Sponsor Brand (RBAC)
  createSponsorBrand: async (payload) => {
    const response = await api.post('/api/v1/edits/sponsor-brand', payload);
    return response.data;
  },

  updateSponsorBrand: async (brandId, payload) => {
    const response = await api.put(`/api/v1/edits/sponsor-brand/${brandId}`, payload);
    return response.data;
  }
};
