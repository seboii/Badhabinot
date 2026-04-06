import { apiClient } from '@/api/client'
import type {
  ConsentResponse,
  SettingsResponse,
  UpdateConsentsRequest,
  UpdateProfileRequest,
  UpdateSettingsRequest,
  UserContextResponse,
  UserProfileResponse,
} from '@/types/user'

export const userApi = {
  async getMe() {
    const response = await apiClient.get<UserContextResponse>('/api/v1/users/me')
    return response.data
  },

  async updateProfile(payload: UpdateProfileRequest) {
    const response = await apiClient.put<UserProfileResponse>('/api/v1/users/me', payload)
    return response.data
  },

  async getSettings() {
    const response = await apiClient.get<SettingsResponse>('/api/v1/users/me/settings')
    return response.data
  },

  async updateSettings(payload: UpdateSettingsRequest) {
    const response = await apiClient.put<SettingsResponse>('/api/v1/users/me/settings', payload)
    return response.data
  },

  async getConsents() {
    const response = await apiClient.get<ConsentResponse>('/api/v1/users/me/consents')
    return response.data
  },

  async updateConsents(payload: UpdateConsentsRequest) {
    const response = await apiClient.put<ConsentResponse>('/api/v1/users/me/consents', payload)
    return response.data
  },
}

