import { apiClient as api } from './client';

export const editsApi = {
  // Edit Metadata (Eras)
  createEraEdit: async (payload) => {
    const response = await api.post('/api/v1/edits/era', payload);
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
  }
};
