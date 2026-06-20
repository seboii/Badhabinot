import { useCallback } from 'react'
import { useAuthStore } from '@/store/auth-store'
import { initialisePushNotifications, teardownPushNotifications } from '@/services/pushNotification'
import type { TokenResponse } from '@/types/auth'

export function useAuth() {
  const session = useAuthStore((state) => state.session)
  const hasHydrated = useAuthStore((state) => state.has_hydrated)
  const _setSession = useAuthStore((state) => state.setSession)
  const _clearSession = useAuthStore((state) => state.clearSession)

  const setSession = useCallback((newSession: TokenResponse) => {
    _setSession(newSession)
    // Registers FCM token on native after login/refresh
    void initialisePushNotifications()
  }, [_setSession])

  const clearSession = useCallback(() => {
    _clearSession()
    void teardownPushNotifications()
  }, [_clearSession])

  return {
    session,
    hasHydrated,
    isAuthenticated: Boolean(session?.access_token),
    isAdmin: (session?.user.role ?? '').toUpperCase() === 'ADMIN',
    setSession,
    clearSession,
  }
}
