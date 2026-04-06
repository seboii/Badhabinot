import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { LoadingScreen } from '@/components/ui/loading-state'
import { useAuth } from '@/hooks/use-auth'

export function ProtectedRoute() {
  const location = useLocation()
  const { hasHydrated, isAuthenticated } = useAuth()

  if (!hasHydrated) {
    return <LoadingScreen message="Restoring your session" />
  }

  if (!isAuthenticated) {
    return <Navigate replace to="/login" state={{ from: location.pathname }} />
  }

  return <Outlet />
}

