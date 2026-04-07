import { Activity, Cigarette, Hand, ShieldAlert } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/empty-state'
import { useLanguage } from '@/i18n/language-provider'
import { behaviorLabel, formatClock, formatRelativeTime, severityLabel } from '@/lib/format'
import type { BehaviorEventResponse } from '@/types/monitoring'

function iconFor(eventType: string) {
  switch (eventType) {
    case 'poor_posture':
      return ShieldAlert
    case 'hand_movement_pattern':
      return Hand
    case 'smoking_like_gesture':
      return Cigarette
    default:
      return Activity
  }
}

function severityVariant(severity: BehaviorEventResponse['severity']) {
  switch (severity) {
    case 'high':
      return 'danger' as const
    case 'medium':
      return 'warning' as const
    default:
      return 'info' as const
  }
}

export function BehaviorEventListCard({
  title,
  description,
  events,
}: {
  title: string
  description: string
  events: BehaviorEventResponse[]
}) {
  const { language, isTurkish } = useLanguage()

  if (events.length === 0) {
    return (
      <EmptyState
        icon={Activity}
        title={isTurkish ? 'Henuz davranis olayi yok' : 'No behavior events yet'}
        description={
          isTurkish
            ? 'Normalize olay akisinin dolmasi icin canli izleme baslat ve birkac kare analiz et.'
            : 'Start live monitoring and analyze a few frames to populate the normalized event stream.'
        }
      />
    )
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          <CardDescription className="mt-2">{description}</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {events.map((event) => {
          const Icon = iconFor(event.event_type)
          return (
            <div
              key={event.event_id}
              className="flex items-start gap-4 rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4"
            >
              <div className="mt-1 flex size-11 shrink-0 items-center justify-center rounded-2xl bg-[rgba(255,255,255,0.06)]">
                <Icon className="size-5 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-semibold text-white">{behaviorLabel(event.event_type, language)}</p>
                  <Badge variant={severityVariant(event.severity)}>{severityLabel(event.severity, language)}</Badge>
                </div>
                <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">{event.interpretation}</p>
                <p className="mt-2 text-sm text-white">{event.recommendation_hint}</p>
                <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--text-soft)]">
                  <span>{formatClock(event.occurred_at, language)}</span>
                  <span>{formatRelativeTime(event.occurred_at, language)}</span>
                  <span>{isTurkish ? 'Guven' : 'Confidence'} {Math.round(event.confidence * 100)}%</span>
                  <span>{event.detector}</span>
                </div>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
