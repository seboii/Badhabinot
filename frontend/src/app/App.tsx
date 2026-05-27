import { useEffect } from 'react'
import { App as CapApp } from '@capacitor/app'
import { StatusBar, Style } from '@capacitor/status-bar'
import { SplashScreen } from '@capacitor/splash-screen'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { AppProviders } from '@/app/providers'
import { AppRouter } from '@/app/router'
import { platform } from '@/lib/platform'

function NativeBootstrap() {
  useEffect(() => {
    if (!platform.isNative) return

    // Dark status bar
    void StatusBar.setStyle({ style: Style.Dark })
    void StatusBar.setBackgroundColor({ color: '#0a0a0f' })

    // Hide splash once React has mounted
    void SplashScreen.hide()

    // Android back button: navigate back or exit
    const listenerPromise = CapApp.addListener('backButton', ({ canGoBack }) => {
      if (canGoBack) {
        window.history.back()
      } else {
        void CapApp.exitApp()
      }
    })

    return () => {
      void listenerPromise.then((h) => h.remove())
    }
  }, [])

  return null
}

export default function App() {
  return (
    <ErrorBoundary>
      <AppProviders>
        <NativeBootstrap />
        <AppRouter />
      </AppProviders>
    </ErrorBoundary>
  )
}
