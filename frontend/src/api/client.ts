import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { env } from '@/lib/env'
import { useAuthStore } from '@/store/auth-store'
import type { TokenResponse } from '@/types/auth'

export class AppApiError extends Error {
  status?: number
  code?: string
  details?: unknown

  constructor(message: string, status?: number, code?: string, details?: unknown) {
    super(message)
    this.name = 'AppApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

type RetryableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean
}

const baseURL = env.apiBaseUrl || ''

export const apiClient = axios.create({
  baseURL,
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

const refreshClient = axios.create({
  baseURL,
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

let refreshPromise: Promise<TokenResponse | null> | null = null

function parseError(error: unknown) {
  if (error instanceof AppApiError) {
    return error
  }

  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    const payload = error.response?.data

    if (payload && typeof payload === 'object') {
      const maybeMessage =
        'message' in payload
          ? payload.message
          : 'error_description' in payload
            ? payload.error_description
            : 'error' in payload
              ? payload.error
              : undefined

      const maybeCode = 'code' in payload ? String(payload.code) : undefined

      return new AppApiError(
        typeof maybeMessage === 'string' ? maybeMessage : error.message,
        status,
        maybeCode,
        payload,
      )
    }

    if (typeof payload === 'string' && payload.length > 0) {
      return new AppApiError(payload, status)
    }

    return new AppApiError(error.message || 'Request failed', status)
  }

  if (error instanceof Error) {
    return new AppApiError(error.message)
  }

  return new AppApiError('Unexpected client error')
}

async function performRefresh() {
  const refreshToken = useAuthStore.getState().session?.refresh_token

  if (!refreshToken) {
    return null
  }

  try {
    const response = await refreshClient.post<TokenResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    })

    useAuthStore.getState().setSession(response.data)
    return response.data
  } catch (error) {
    useAuthStore.getState().clearSession()
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.assign('/login')
    }
    throw parseError(error)
  }
}

apiClient.interceptors.request.use((config) => {
  const accessToken = useAuthStore.getState().session?.access_token

  if (accessToken) {
    config.headers.set('Authorization', `Bearer ${accessToken}`)
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const request = error.config as RetryableRequestConfig | undefined
    const status = error.response?.status
    const url = request?.url ?? ''
    const isAuthRoute =
      url.includes('/api/v1/auth/login') ||
      url.includes('/api/v1/auth/register') ||
      url.includes('/api/v1/auth/refresh')

    if (!request || request._retry || status !== 401 || isAuthRoute) {
      return Promise.reject(parseError(error))
    }

    request._retry = true

    try {
      refreshPromise ??= performRefresh().finally(() => {
        refreshPromise = null
      })

      const session = await refreshPromise
      if (!session) {
        return Promise.reject(parseError(error))
      }

      request.headers.set('Authorization', `Bearer ${session.access_token}`)
      return apiClient(request)
    } catch (refreshError) {
      return Promise.reject(parseError(refreshError))
    }
  },
)

export function toErrorMessage(error: unknown, fallback = 'Something went wrong') {
  return parseError(error).message || fallback
}

