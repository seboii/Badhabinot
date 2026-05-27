import { PushNotifications } from '@capacitor/push-notifications'
import { platform } from '@/lib/platform'
import { apiClient } from '@/api/client'

/**
 * Initialise FCM push notifications on native platforms.
 * Call this once after successful login (setSession).
 */
export async function initialisePushNotifications(): Promise<void> {
  if (!platform.isNative) return

  // Request permission
  const permission = await PushNotifications.requestPermissions()
  if (permission.receive !== 'granted') return

  await PushNotifications.register()

  // Send FCM token to backend
  await PushNotifications.addListener('registration', async (token) => {
    try {
      await apiClient.post('/api/v1/monitoring/push/register', {
        token: token.value,
        platform: platform.name,
      })
    } catch (err) {
      console.warn('[Push] Failed to register token with backend:', err)
    }
  })

  PushNotifications.addListener('registrationError', (err) => {
    console.error('[Push] Registration error:', err)
  })

  // Foreground notification display
  PushNotifications.addListener('pushNotificationReceived', (notification) => {
    console.log('[Push] Notification received in foreground:', notification)
  })

  // Notification tap handler
  PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
    console.log('[Push] Notification action performed:', action)
  })
}

export async function teardownPushNotifications(): Promise<void> {
  if (!platform.isNative) return
  await PushNotifications.removeAllListeners()
}
