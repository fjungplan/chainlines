import { apiClient } from './client';

const API_BASE = '/api/v1/admin/users';

export const getUsers = async ({ page = 1, limit = 50, search = '' }) => {
    const skip = (page - 1) * limit;
    const params = { skip, limit };
    if (search) params.search = search;

    const response = await apiClient.get(API_BASE, { params });
    return response.data;
};

export const updateUser = async (userId, data) => {
    const response = await apiClient.patch(`${API_BASE}/${userId}`, data);
    return response.data;
};
