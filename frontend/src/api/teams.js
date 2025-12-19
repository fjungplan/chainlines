import apiClient from './client';

export const teamsApi = {
  getTimeline: async (params) => {
    const response = await apiClient.get('/api/v1/timeline', { params });
    return response.data;
  },

  getTeamHistory: async (nodeId) => {
    const response = await apiClient.get(`/api/v1/teams/${nodeId}/history`);
    return response.data;
  },

  getTeams: async (params) => {
    const response = await apiClient.get('/api/v1/teams', { params });
    return response.data;
  },

  getTeam: async (nodeId) => {
    const response = await apiClient.get(`/api/v1/teams/${nodeId}`);
    return response.data;
  },

  createTeamNode: async (data) => {
    const response = await apiClient.post('/api/v1/teams', data);
    return response.data;
  },

  updateTeamNode: async (nodeId, data) => {
    const response = await apiClient.put(`/api/v1/teams/${nodeId}`, data);
    return response.data;
  },

  deleteTeamNode: async (nodeId) => {
    const response = await apiClient.delete(`/api/v1/teams/${nodeId}`);
    return response.data;
  },

  getTeamEras: async (nodeId, params) => {
    const response = await apiClient.get(`/api/v1/teams/${nodeId}/eras`, { params });
    return response.data;
  },

  createTeamEra: async (nodeId, data) => {
    const response = await apiClient.post(`/api/v1/teams/${nodeId}/eras`, data);
    return response.data;
  },

  updateTeamEra: async (eraId, data) => {
    const response = await apiClient.put(`/api/v1/teams/eras/${eraId}`, data);
    return response.data;
  },

  deleteTeamEra: async (eraId) => {
    const response = await apiClient.delete(`/api/v1/teams/eras/${eraId}`);
    return response.data;
  },
};
