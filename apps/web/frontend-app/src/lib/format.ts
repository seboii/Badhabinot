import { parseISO } from 'date-fns'
import type { AppLanguage } from '@/i18n/language-provider'

function toDate(value: Date | string | null | undefined) {
  if (!value) {
    return null
  }

  const date = typeof value === 'string' ? parseISO(value) : value
  return Number.isNaN(date.getTime()) ? null : date
}

function localeCode(language: AppLanguage) {
  return language === 'tr' ? 'tr-TR' : 'en-US'
}

export function formatDateTime(value: Date | string | null | undefined, language: AppLanguage = 'en') {
  const date = toDate(value)
  if (!date) {
    return language === 'tr' ? 'Bilinmiyor' : 'Unknown'
  }

  return new Intl.DateTimeFormat(localeCode(language), {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatClock(value: Date | string | null | undefined, language: AppLanguage = 'en') {
  const date = toDate(value)
  if (!date) {
    return language === 'tr' ? 'Bilinmiyor' : 'Unknown'
  }

  return new Intl.DateTimeFormat(localeCode(language), {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export function formatRelativeTime(value: Date | string | null | undefined, language: AppLanguage = 'en') {
  const date = toDate(value)
  if (!date) {
    return language === 'tr' ? 'Bilinmiyor' : 'Unknown'
  }

  const now = Date.now()
  const diffSeconds = Math.round((date.getTime() - now) / 1000)
  const absSeconds = Math.abs(diffSeconds)
  const formatter = new Intl.RelativeTimeFormat(localeCode(language), { numeric: 'auto' })

  if (absSeconds < 60) {
    return formatter.format(diffSeconds, 'second')
  }

  const diffMinutes = Math.round(diffSeconds / 60)
  if (Math.abs(diffMinutes) < 60) {
    return formatter.format(diffMinutes, 'minute')
  }

  const diffHours = Math.round(diffMinutes / 60)
  if (Math.abs(diffHours) < 24) {
    return formatter.format(diffHours, 'hour')
  }

  const diffDays = Math.round(diffHours / 24)
  return formatter.format(diffDays, 'day')
}

export function formatMilliliters(value: number | null | undefined, language: AppLanguage = 'en') {
  if (value == null) {
    return language === 'tr' ? '0 ml' : '0 ml'
  }

  return `${new Intl.NumberFormat(localeCode(language)).format(value)} ml`
}

export function behaviorLabel(value: string | null | undefined, language: AppLanguage = 'en') {
  const isTurkish = language === 'tr'

  switch ((value || '').toLowerCase()) {
    case 'nail_biting':
      return isTurkish ? 'Tirnak yeme' : 'Nail biting'
    case 'smoking':
      return isTurkish ? 'Sigara jesti' : 'Smoking gesture'
    case 'smoking_like_gesture':
      return isTurkish ? 'Sigara benzeri isaret' : 'Smoking-like cue'
    case 'hand_movement_pattern':
      return isTurkish ? 'El hareketi paterni' : 'Hand movement pattern'
    case 'poor_posture':
      return isTurkish ? 'Kotu durus' : 'Poor posture'
    case 'posture_reminder':
      return isTurkish ? 'Durus hatirlaticisi' : 'Posture reminder'
    case 'mindful_break_reminder':
      return isTurkish ? 'Farkindalik molasi hatirlaticisi' : 'Mindful break reminder'
    case 'monitoring_started':
      return isTurkish ? 'Izleme basladi' : 'Monitoring started'
    case 'monitoring_stopped':
      return isTurkish ? 'Izleme durdu' : 'Monitoring stopped'
    case 'water_reminder':
    case 'water':
      return isTurkish ? 'Su hatirlaticisi' : 'Water reminder'
    case 'break':
    case 'break_reminder':
    case 'exercise':
      return isTurkish ? 'Mola hatirlaticisi' : 'Break reminder'
    case 'water_logged':
      return isTurkish ? 'Su kaydi' : 'Hydration log'
    case 'none':
      return isTurkish ? 'Riskli davranis yok' : 'No risky behavior'
    default:
      return value
        ? value
            .replace(/_/g, ' ')
            .replace(/\b\w/g, (character) => character.toUpperCase())
        : isTurkish
          ? 'Bilinmiyor'
          : 'Unknown'
  }
}

export function postureLabel(value: string | null | undefined, language: AppLanguage = 'en') {
  const isTurkish = language === 'tr'

  switch ((value || '').toLowerCase()) {
    case 'poor':
      return isTurkish ? 'Duzeltme gerekli' : 'Needs adjustment'
    case 'good':
      return isTurkish ? 'Durus hizali' : 'Aligned posture'
    default:
      return isTurkish ? 'Kullanilamiyor' : 'Unavailable'
  }
}

export function severityLabel(value: string | null | undefined, language: AppLanguage = 'en') {
  const isTurkish = language === 'tr'

  switch ((value || '').toLowerCase()) {
    case 'high':
      return isTurkish ? 'Yuksek' : 'High'
    case 'medium':
      return isTurkish ? 'Orta' : 'Medium'
    case 'low':
      return isTurkish ? 'Dusuk' : 'Low'
    default:
      return isTurkish ? 'Bilinmiyor' : 'Unknown'
  }
}

export function toPercent(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return '0%'
  }

  return `${Math.round(value * 100)}%`
}
