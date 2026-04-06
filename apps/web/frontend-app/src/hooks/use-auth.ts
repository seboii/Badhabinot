import { useAuthStore } from '@/store/auth-store'

export function useAuth() {
  const session = useAuthStore((state) => state.session)
  const hasHydrated = useAuthStore((state) => state.has_hydrated)
  const setSession = useAuthStore((state) => state.setSession)
  const clearSession = useAuthStore((state) => state.clearSession)

  return {
    session,
    hasHydrated,
    isAuthenticated: Boolean(session?.access_token),
    setSession,
    clearSession,
  }
}

