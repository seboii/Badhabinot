import { Suspense, lazy, type ReactNode } from 'react'
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { PublicOnlyRoute } from '@/components/layout/PublicOnlyRoute'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { AppShell } from '@/components/layout/AppShell'
import { LoadingScreen } from '@/components/ui/loading-state'
import { userApi } from '@/api/user'

const DashboardPage = lazy(async () => {
  const module = await import('@/pages/DashboardPage')
  return { default: module.DashboardPage }
})

const HistoryPage = lazy(async () => {
  const module = await import('@/pages/HistoryPage')
  return { default: module.HistoryPage }
})

const LoginPage = lazy(async () => {
  const module = await import('@/pages/LoginPage')
  return { default: module.LoginPage }
})

const NotFoundPage = lazy(async () => {
  const module = await import('@/pages/NotFoundPage')
  return { default: module.NotFoundPage }
})

const OnboardingPage = lazy(async () => {
  const module = await import('@/pages/OnboardingPage')
  return { default: module.OnboardingPage }
})

const RegisterPage = lazy(async () => {
  const module = await import('@/pages/RegisterPage')
  return { default: module.RegisterPage }
})

const SettingsPage = lazy(async () => {
  const module = await import('@/pages/SettingsPage')
  return { default: module.SettingsPage }
})

function LazyRoute({ children }: { children: ReactNode }) {
  return <Suspense fallback={<LoadingScreen message="Loading page" />}>{children}</Suspense>
}

function HomeRedirect() {
  const { data, isLoading } = useQuery({
    queryKey: ['user-context'],
    queryFn: userApi.getMe,
  })

  if (isLoading) {
    return <LoadingScreen message="Preparing your workspace" />
  }

  const needsOnboarding =
    !data?.consents.privacy_policy_accepted || !data?.consents.camera_monitoring_accepted

  return <Navigate replace to={needsOnboarding ? '/onboarding' : '/dashboard'} />
}

function ShellOutlet() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  )
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<LazyRoute><LoginPage /></LazyRoute>} />
          <Route path="/register" element={<LazyRoute><RegisterPage /></LazyRoute>} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route path="/onboarding" element={<LazyRoute><OnboardingPage /></LazyRoute>} />
          <Route element={<ShellOutlet />}>
            <Route index element={<HomeRedirect />} />
            <Route path="/dashboard" element={<LazyRoute><DashboardPage /></LazyRoute>} />
            <Route path="/history" element={<LazyRoute><HistoryPage /></LazyRoute>} />
            <Route path="/settings" element={<LazyRoute><SettingsPage /></LazyRoute>} />
          </Route>
        </Route>

        <Route path="*" element={<LazyRoute><NotFoundPage /></LazyRoute>} />
      </Routes>
    </BrowserRouter>
  )
}
