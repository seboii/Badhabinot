import { Suspense, lazy, type ReactNode } from 'react'
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { PublicOnlyRoute } from '@/components/layout/PublicOnlyRoute'
import { ProtectedRoute } from '@/components/layout/ProtectedRoute'
import { AppShell } from '@/components/layout/AppShell'
import { LoadingScreen } from '@/components/ui/loading-state'
import { useLanguage } from '@/i18n/language-provider'

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

const RegisterPage = lazy(async () => {
  const module = await import('@/pages/RegisterPage')
  return { default: module.RegisterPage }
})

const ForgotPasswordPage = lazy(async () => {
  const module = await import('@/pages/ForgotPasswordPage')
  return { default: module.ForgotPasswordPage }
})

const ResetPasswordPage = lazy(async () => {
  const module = await import('@/pages/ResetPasswordPage')
  return { default: module.ResetPasswordPage }
})

const SettingsPage = lazy(async () => {
  const module = await import('@/pages/SettingsPage')
  return { default: module.SettingsPage }
})

const AdminPage = lazy(async () => {
  const module = await import('@/pages/AdminPage')
  return { default: module.AdminPage }
})

const KvkkPage = lazy(async () => {
  const module = await import('@/pages/KvkkPage')
  return { default: module.KvkkPage }
})

function LazyRoute({ children, message }: { children: ReactNode; message: string }) {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingScreen message={message} />}>{children}</Suspense>
    </ErrorBoundary>
  )
}

function HomeRedirect() {
  return <Navigate replace to="/dashboard" />
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
          <Route path="/forgot-password" element={<LazyRoute message={loadingMessage}><ForgotPasswordPage /></LazyRoute>} />
          <Route path="/reset-password" element={<LazyRoute message={loadingMessage}><ResetPasswordPage /></LazyRoute>} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route element={<ShellOutlet />}>
            <Route index element={<HomeRedirect />} />
            <Route path="/dashboard" element={<LazyRoute message={loadingMessage}><DashboardPage /></LazyRoute>} />
            <Route path="/history" element={<LazyRoute message={loadingMessage}><HistoryPage /></LazyRoute>} />
            <Route path="/reports" element={<LazyRoute message={loadingMessage}><ReportsPage /></LazyRoute>} />
            <Route path="/chat" element={<LazyRoute message={loadingMessage}><ChatPage /></LazyRoute>} />
            <Route path="/settings" element={<LazyRoute message={loadingMessage}><SettingsPage /></LazyRoute>} />
            <Route path="/admin" element={<LazyRoute message={loadingMessage}><AdminPage /></LazyRoute>} />
          </Route>
        </Route>

        <Route path="/kvkk" element={<LazyRoute message={loadingMessage}><KvkkPage /></LazyRoute>} />
        <Route path="/privacy" element={<LazyRoute message={loadingMessage}><KvkkPage /></LazyRoute>} />
        <Route path="*" element={<LazyRoute message={loadingMessage}><NotFoundPage /></LazyRoute>} />
      </Routes>
    </BrowserRouter>
  )
}
