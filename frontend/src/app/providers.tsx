import type { PropsWithChildren } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { LanguageProvider } from '@/i18n/language-provider'
import { ThemeProvider, useTheme } from '@/theme/theme-provider'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      refetchOnWindowFocus: false,
      retry(failureCount, error) {
        const status = typeof error === 'object' && error && 'status' in error ? Number(error.status) : undefined
        if (status === 401 || status === 403 || status === 404) {
          return false
        }
        return failureCount < 1
      },
    },
    mutations: {
      retry: false,
    },
  },
})

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <LanguageProvider>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          {children}
          <AppToaster />
        </QueryClientProvider>
      </ThemeProvider>
    </LanguageProvider>
  )
}

function AppToaster() {
  const { theme } = useTheme()

  return <Toaster richColors theme={theme} position="top-right" />
}
