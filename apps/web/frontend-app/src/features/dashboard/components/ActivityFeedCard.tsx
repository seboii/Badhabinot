import { BellRing, GlassWater, ShieldAlert, TimerReset, Waves } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EmptyState } from '@/components/ui/empty-state'
import { Badge } from '@/components/ui/badge'
import { behaviorLabel, formatClock, formatRelativeTime } from '@/lib/format'
import type { ActivityItemResponse } from '@/types/monitoring'

function itemIcon(activityType: string) {
  switch (activityType) {
    case 'water_logged':
      return GlassWater
    case 'water':
    case 'water_reminder':
      return Waves
    case 'break':
    case 'break_reminder':
    case 'exercise':
      return TimerReset
    case 'poor_posture':
    case 'nail_biting':
    case 'smoking':
      return ShieldAlert
    default:
      return BellRing
  }
}

function categoryVariant(category: ActivityItemResponse['category']) {
  switch (category) {
    case 'ALERT':
      return 'danger' as const
    case 'REMINDER':
      return 'warning' as const
    case 'MANUAL':
      return 'info' as const
    default:
      return 'neutral' as const
  }
}

export function ActivityFeedCard({
  title,
  description,
  items,
}: {
  title: string
  description: string
  items: ActivityItemResponse[]
}) {
  if (items.length === 0) {
    return (
      <EmptyState
        icon={BellRing}
        title="No activity yet"
        description="Start a monitoring session or log a reminder to populate the activity feed."
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
        {items.map((item) => {
          const Icon = itemIcon(item.activity_type)
          return (
            <div
              key={item.id}
              className="flex items-start gap-4 rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4"
            >
              <div className="mt-1 flex size-11 shrink-0 items-center justify-center rounded-2xl bg-[rgba(255,255,255,0.06)]">
                <Icon className="size-5 text-white" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-semibold text-white">{item.title || behaviorLabel(item.activity_type)}</p>
                  <Badge variant={categoryVariant(item.category)}>{item.category}</Badge>
                </div>
                <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">{item.message}</p>
                <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-[var(--text-soft)]">
                  <span>{formatClock(item.occurred_at)}</span>
                  <span>{formatRelativeTime(item.occurred_at)}</span>
                  {item.confidence != null ? <span>Confidence {Math.round(item.confidence * 100)}%</span> : null}
                </div>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

