import { toast } from 'sonner'
import { platform } from '@/lib/platform'

/**
 * Hatırlatıcı alarmı: ses (WebAudio bip) + titreşim (Haptics) + sistem bildirimi
 * (native LocalNotifications) + uygulama içi toast. Mobilde bir hatırlatıcı
 * geldiğinde "bildirim düşsün + alarm çalsın" davranışı için tek giriş noktası.
 *
 * Web'de: WebAudio + toast (+ tarayıcı titreşimi varsa).
 * Native'de: WebAudio + Haptics titreşim + sistem bildirimi + toast.
 */

let _audioCtx: AudioContext | null = null

function getAudioContext(): AudioContext | null {
  try {
    if (typeof window === 'undefined') return null
    const Ctor = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!Ctor) return null
    if (!_audioCtx) _audioCtx = new Ctor()
    if (_audioCtx.state === 'suspended') void _audioCtx.resume()
    return _audioCtx
  } catch {
    return null
  }
}

/** Kısa, dikkat çekici alarm tonu (varsayılan 3 bip). Ek dosya gerektirmez. */
export function playAlarmSound(beeps = 3): void {
  const ctx = getAudioContext()
  if (!ctx) return
  const start = ctx.currentTime
  for (let i = 0; i < beeps; i++) {
    const t = start + i * 0.45
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'square'
    osc.frequency.setValueAtTime(i % 2 === 0 ? 880 : 988, t)
    gain.gain.setValueAtTime(0.0001, t)
    gain.gain.exponentialRampToValueAtTime(0.25, t + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.32)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(t)
    osc.stop(t + 0.34)
  }
}

async function vibrate(): Promise<void> {
  if (platform.isNative) {
    try {
      const { Haptics } = await import('@capacitor/haptics')
      await Haptics.vibrate({ duration: 600 })
      await Haptics.vibrate({ duration: 600 })
    } catch {
      /* haptics yoksa sessiz geç */
    }
    return
  }
  try {
    navigator.vibrate?.([300, 150, 300, 150, 400])
  } catch {
    /* tarayıcı desteklemiyorsa geç */
  }
}

/** Native'de yerel bildirim iznini ister (giriş sonrası bir kez çağrılır). */
export async function ensureReminderPermissions(): Promise<void> {
  if (!platform.isNative) return
  try {
    const { LocalNotifications } = await import('@capacitor/local-notifications')
    const perm = await LocalNotifications.checkPermissions()
    if (perm.display !== 'granted') {
      await LocalNotifications.requestPermissions()
    }
  } catch {
    /* eklenti senkronize değilse sessiz geç */
  }
}

/**
 * Bir hatırlatıcı geldiğinde alarmı tetikler: ses + titreşim + (native) sistem
 * bildirimi + toast. Hem foreground push hem uygulama içi hatırlatıcılar için.
 */
export async function fireReminder(title: string, body = ''): Promise<void> {
  playAlarmSound()
  void vibrate()
  toast.warning(title, { description: body || undefined, duration: 8000 })

  if (platform.isNative) {
    try {
      const { LocalNotifications } = await import('@capacitor/local-notifications')
      await LocalNotifications.schedule({
        notifications: [
          {
            id: Date.now() % 2_000_000_000,
            title,
            body,
            schedule: { at: new Date(Date.now() + 150) },
          },
        ],
      })
    } catch {
      /* web stub / native senkron edilmemiş → toast + ses yeterli */
    }
  }
}
