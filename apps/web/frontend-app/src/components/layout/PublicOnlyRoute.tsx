import { Navigate, Outlet } from 'react-router-dom'
import { LoadingScreen } from '@/components/ui/loading-state'
import { useAuth } from '@/hooks/use-auth'
import { useLanguage } from '@/i18n/language-provider'

export function PublicOnlyRoute() {
  const { isTurkish } = useLanguage()
  const { hasHydrated, isAuthenticated } = useAuth()

  if (!hasHydrated) {
    return <LoadingScreen message={isTurkish ? 'Oturum kontrol ediliyor' : 'Checking your session'} />
  }

  if (isAuthenticated) {
    return <Navigate replace to="/" />
  }

  return <Outlet />
}
