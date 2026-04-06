import { Navigate, Outlet } from 'react-router-dom'
import { LoadingScreen } from '@/components/ui/loading-state'
import { useAuth } from '@/hooks/use-auth'

export function PublicOnlyRoute() {
  const { hasHydrated, isAuthenticated } = useAuth()

  if (!hasHydrated) {
    return <LoadingScreen message="Checking your session" />
  }

  if (isAuthenticated) {
    return <Navigate replace to="/" />
  }

  return <Outlet />
}

