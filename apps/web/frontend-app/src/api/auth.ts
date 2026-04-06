import { apiClient } from '@/api/client'
import type {
  AuthenticatedUserResponse,
  LoginRequest,
  LogoutRequest,
  RegisterRequest,
  TokenResponse,
} from '@/types/auth'

export const authApi = {
  async register(payload: RegisterRequest) {
    const response = await apiClient.post<TokenResponse>('/api/v1/auth/register', payload)
    return response.data
  },

  async login(payload: LoginRequest) {
    const response = await apiClient.post<TokenResponse>('/api/v1/auth/login', payload)
    return response.data
  },

  async me() {
    const response = await apiClient.get<AuthenticatedUserResponse>('/api/v1/auth/me')
    return response.data
  },

  async logout(payload: LogoutRequest) {
    await apiClient.post('/api/v1/auth/logout', payload)
  },
}

