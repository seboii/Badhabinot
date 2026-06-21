import { apiClient } from '@/api/client'
import type {
  AdminReportSummary,
  AdminStats,
  AdminUserAiSettingsRequest,
  AdminUserDetail,
  AdminUserListResponse,
} from '@/types/admin'

export const adminApi = {
  async getStats() {
    const response = await apiClient.get<AdminStats>('/api/v1/admin/stats')
    return response.data
  },

  async listUsers(params: { search?: string; page?: number; size?: number } = {}) {
    const response = await apiClient.get<AdminUserListResponse>('/api/v1/admin/users', {
      params: {
        search: params.search || undefined,
        page: params.page ?? 0,
        size: params.size ?? 20,
      },
    })
    return response.data
  },

  async getUser(userId: string) {
    const response = await apiClient.get<AdminUserDetail>(`/api/v1/admin/users/${userId}`)
    return response.data
  },

  async getUserReports(userId: string, limit = 30) {
    const response = await apiClient.get<AdminReportSummary[]>(`/api/v1/admin/users/${userId}/reports`, {
      params: { limit },
    })
    return response.data
  },

  async deleteUser(userId: string) {
    await apiClient.delete(`/api/v1/admin/users/${userId}`)
  },

  async resetUserData(userId: string) {
    await apiClient.post(`/api/v1/admin/users/${userId}/reset`)
  },

  async approveUser(userId: string) {
    await apiClient.post(`/api/v1/admin/users/${userId}/approve`)
  },

  async updateUserAiSettings(userId: string, body: AdminUserAiSettingsRequest) {
    await apiClient.put(`/api/v1/admin/users/${userId}/ai-settings`, body)
  },
}
