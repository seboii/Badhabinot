import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.badhabinot.app',
  appName: 'Badhabinot',
  webDir: 'dist',
  // For local development: points webview to the running Vite/Nginx dev server.
  // Remove (or comment out) server.url before a production release build.
  server: {
    url: 'http://192.168.1.26',
    cleartext: true,
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      launchAutoHide: true,
      backgroundColor: '#0a0a0f',
      showSpinner: false,
    },
    StatusBar: {
      style: 'Dark',
      backgroundColor: '#0a0a0f',
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert'],
    },
  },
}

export default config
