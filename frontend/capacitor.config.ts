import type { CapacitorConfig } from '@capacitor/cli'

// Geliştirmede canlı sunucuya bağlanmak için CAP_SERVER_URL ortam değişkenini ver:
//   CAP_SERVER_URL=http://192.168.1.26 npm run android:sync
// (emülatör için http://10.0.2.2). Üretim APK'sı için CAP_SERVER_URL'i BOŞ bırak →
// `dist` klasörü APK'ya gömülür ve uygulama sunucusuz/çevrimdışı çalışır.
const devServerUrl = process.env.CAP_SERVER_URL?.trim()

const config: CapacitorConfig = {
  appId: 'com.badhabinot.app',
  appName: 'Badhabinot',
  webDir: 'dist',
  // server bloğu yalnızca CAP_SERVER_URL verildiğinde eklenir.
  ...(devServerUrl
    ? { server: { url: devServerUrl, cleartext: true } }
    : {}),
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
