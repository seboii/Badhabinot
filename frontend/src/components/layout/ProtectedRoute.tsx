import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { LoadingScreen } from '@/components/ui/loading-state'
import { useAuth } from '@/hooks/use-auth'
import { useLanguage } from '@/i18n/language-provider'

export function ProtectedRoute() {
  const { isTurkish } = useLanguage()
  const location = useLocation()
  const { hasHydrated, isAuthenticated } = useAuth()

  if (!hasHydrated) {
    return <LoadingScreen message={isTurkish ? 'Oturum geri yukleniyor' : 'Restoring your session'} />
  }

  if (!isAuthenticated) {
    return <Navigate replace to="/login" state={{ from: location.pathname }} />
  }

  return <Outlet />
}
