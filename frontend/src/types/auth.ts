export type TokenUserSummary = {
  id: string
  email: string
  role: string
}

export type TokenResponse = {
  access_token: string
  access_token_expires_at: string
  refresh_token: string
  refresh_token_expires_at: string
  user: TokenUserSummary
}

export type AuthenticatedUserResponse = {
  user_id: string
  email: string
  roles: string[]
  issued_at: string
  expires_at: string
}

export type RegisterRequest = {
  email: string
  password: string
  display_name: string
  timezone: string
  locale: string
}

export type RegisterResponse = {
  pending_approval: boolean
  message: string
  session: TokenResponse | null
}

export type LoginRequest = {
  email: string
  password: string
}

export type RefreshTokenRequest = {
  refresh_token: string
}

export type LogoutRequest = {
  refresh_token: string
}

export type PasswordResetRequestDto = {
  email: string
}

export type PasswordResetConfirmDto = {
  token: string
  new_password: string
}

export type FaceLoginRequest = {
  email: string
  face_image_base64: string
  image_content_type: string
}

export type FaceLoginErrorCode =
  | 'FACE_NOT_REGISTERED'
  | 'FACE_MISMATCH'
  | 'too_many_login_attempts'
  | 'unauthorized'

