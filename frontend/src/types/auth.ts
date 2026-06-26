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
  captcha_token: string
}

export type CaptchaChallenge = {
  captcha_id: string
  prompt_tr: string
  prompt_en: string
  tiles: string[]
}

export type CaptchaVerifyResponse = {
  token: string
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


