import { Suspense, lazy, type ReactNode } from 'react'
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { PublicOnlyRoute } from '@/components/layout/PublicOnlyRoute'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { AppShell } from '@/components/layout/AppShell'
import { LoadingScreen } from '@/components/ui/loading-state'
import { useLanguage } from '@/i18n/language-provider'
import { userApi } from '@/api/user'

const DashboardPage = lazy(async () => {
  const module = await import('@/pages/DashboardPage')
  return { default: module.DashboardPage }
})

const HistoryPage = lazy(async () => {
  const module = await import('@/pages/HistoryPage')
  return { default: module.HistoryPage }
})

const ReportsPage = lazy(async () => {
  const module = await import('@/pages/ReportsPage')
  return { default: module.ReportsPage }
})

const ChatPage = lazy(async () => {
  const module = await import('@/pages/ChatPage')
  return { default: module.ChatPage }
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

function LazyRoute({ children, message }: { children: ReactNode; message: string }) {
  return <Suspense fallback={<LoadingScreen message={message} />}>{children}</Suspense>
}

function HomeRedirect() {
  const { isTurkish } = useLanguage()
  const { data, isLoading } = useQuery({
    queryKey: ['user-context'],
    queryFn: userApi.getMe,
  })

  if (isLoading) {
    return <LoadingScreen message={isTurkish ? 'Calisma alani hazirlaniyor' : 'Preparing your workspace'} />
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
  const { isTurkish } = useLanguage()
  const loadingMessage = isTurkish ? 'Sayfa yukleniyor' : 'Loading page'

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<LazyRoute message={loadingMessage}><LoginPage /></LazyRoute>} />
          <Route path="/register" element={<LazyRoute message={loadingMessage}><RegisterPage /></LazyRoute>} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route path="/onboarding" element={<LazyRoute message={loadingMessage}><OnboardingPage /></LazyRoute>} />
          <Route element={<ShellOutlet />}>
            <Route index element={<HomeRedirect />} />
            <Route path="/dashboard" element={<LazyRoute message={loadingMessage}><DashboardPage /></LazyRoute>} />
            <Route path="/history" element={<LazyRoute message={loadingMessage}><HistoryPage /></LazyRoute>} />
            <Route path="/reports" element={<LazyRoute message={loadingMessage}><ReportsPage /></LazyRoute>} />
            <Route path="/chat" element={<LazyRoute message={loadingMessage}><ChatPage /></LazyRoute>} />
            <Route path="/settings" element={<LazyRoute message={loadingMessage}><SettingsPage /></LazyRoute>} />
          </Route>
        </Route>

        <Route path="*" element={<LazyRoute message={loadingMessage}><NotFoundPage /></LazyRoute>} />
      </Routes>
    </BrowserRouter>
  )
}
