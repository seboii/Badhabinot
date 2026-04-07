import { format, formatDistanceToNow, parseISO } from 'date-fns'

function toDate(value: Date | string | null | undefined) {
  if (!value) {
    return null
  }

  const date = typeof value === 'string' ? parseISO(value) : value
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDateTime(value: Date | string | null | undefined, pattern = 'dd MMM yyyy, HH:mm') {
  const date = toDate(value)
  return date ? format(date, pattern) : 'Unknown'
}

export function formatClock(value: Date | string | null | undefined) {
  return formatDateTime(value, 'HH:mm')
}

export function formatRelativeTime(value: Date | string | null | undefined) {
  const date = toDate(value)
  return date ? formatDistanceToNow(date, { addSuffix: true }) : 'Unknown'
}

export function formatMilliliters(value: number | null | undefined) {
  if (value == null) {
    return '0 ml'
  }

  return `${new Intl.NumberFormat('en-US').format(value)} ml`
}

export function behaviorLabel(value: string | null | undefined) {
  switch ((value || '').toLowerCase()) {
    case 'nail_biting':
      return 'Nail biting'
    case 'smoking':
      return 'Smoking gesture'
    case 'smoking_like_gesture':
      return 'Smoking-like cue'
    case 'hand_movement_pattern':
      return 'Hand movement pattern'
    case 'poor_posture':
      return 'Poor posture'
    case 'posture_reminder':
      return 'Posture reminder'
    case 'mindful_break_reminder':
      return 'Mindful break reminder'
    case 'monitoring_started':
      return 'Monitoring started'
    case 'monitoring_stopped':
      return 'Monitoring stopped'
    case 'water_reminder':
    case 'water':
      return 'Water reminder'
    case 'break':
    case 'break_reminder':
    case 'exercise':
      return 'Break reminder'
    case 'water_logged':
      return 'Hydration log'
    case 'none':
      return 'No risky behavior'
    default:
      return value
        ? value
            .replace(/_/g, ' ')
            .replace(/\b\w/g, (character) => character.toUpperCase())
        : 'Unknown'
  }
}

export function postureLabel(value: string | null | undefined) {
  switch ((value || '').toLowerCase()) {
    case 'poor':
      return 'Needs adjustment'
    case 'good':
      return 'Aligned posture'
    default:
      return 'Unavailable'
  }
}

export function severityLabel(value: string | null | undefined) {
  switch ((value || '').toLowerCase()) {
    case 'high':
      return 'High'
    case 'medium':
      return 'Medium'
    case 'low':
      return 'Low'
    default:
      return 'Unknown'
  }
}

export function toPercent(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) {
    return '0%'
  }

  return `${Math.round(value * 100)}%`
}
