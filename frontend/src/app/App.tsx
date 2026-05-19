import { ErrorBoundary } from '@/components/ErrorBoundary'
import { AppProviders } from '@/app/providers'
import { AppRouter } from '@/app/router'

export default function App() {
  return (
    <ErrorBoundary>
      <AppProviders>
        <AppRouter />
      </AppProviders>
    </ErrorBoundary>
  )
}

