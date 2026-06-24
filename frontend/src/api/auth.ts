import { apiClient } from '@/api/client'
import type {
  AuthenticatedUserResponse,
  CaptchaChallenge,
  CaptchaVerifyResponse,
  FaceLoginRequest,
  LoginRequest,
  LogoutRequest,
  PasswordResetConfirmDto,
  PasswordResetRequestDto,
  RegisterRequest,
  RegisterResponse,
  TokenResponse,
} from '@/types/auth'

export const authApi = {
  async register(payload: RegisterRequest) {
    const response = await apiClient.post<RegisterResponse>('/api/v1/auth/register', payload)
    return response.data
  },

  async getCaptcha() {
    const response = await apiClient.get<CaptchaChallenge>('/api/v1/auth/captcha')
    return response.data
  },

  async verifyCaptcha(captchaId: string, answer: number[]) {
    const response = await apiClient.post<CaptchaVerifyResponse>('/api/v1/auth/captcha/verify', {
      captcha_id: captchaId,
      answer,
    })
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

  async requestPasswordReset(payload: PasswordResetRequestDto) {
    await apiClient.post('/api/v1/auth/password-reset-request', payload)
  },

  async confirmPasswordReset(payload: PasswordResetConfirmDto) {
    await apiClient.post('/api/v1/auth/password-reset-confirm', payload)
  },

  async loginWithFace(payload: FaceLoginRequest) {
    const response = await apiClient.post<TokenResponse>('/api/v1/auth/login/face', {
      email: payload.email,
      face_image_base64: payload.face_image_base64,
      image_content_type: payload.image_content_type,
    })
    return response.data
  },
}

