import { LoaderCircle } from 'lucide-react'
import { cn } from '@/lib/cn'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { useLanguage } from '@/i18n/language-provider'

function Pulse({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={cn('animate-pulse rounded-2xl bg-[var(--surface-muted)]', className)} style={style} />
}

export function InlineSpinner() {
  return <LoaderCircle className="size-4 animate-spin text-[var(--primary)]" />
}

export function LoadingCard({ message }: { message?: string }) {
  const { isTurkish } = useLanguage()
  const resolved = message || (isTurkish ? 'Veriler yukleniyor' : 'Loading data')

  return (
    <div className="flex min-h-[220px] items-center justify-center rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface)] p-6 text-sm text-[var(--text-muted)]">
      <div className="flex items-center gap-3">
        <InlineSpinner />
        <span>{resolved}</span>
      </div>
    </div>
  )
}

export function MetricCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-3">
            <Pulse className="h-3 w-20" />
            <Pulse className="mt-4 h-8 w-14" />
            <Pulse className="mt-3 h-3 w-36" />
          </div>
          <Pulse className="size-12 flex-none" />
        </div>
      </CardContent>
    </Card>
  )
}

export function ActivityFeedSkeleton() {
  return (
    <Card>
      <CardHeader>
        <div className="space-y-2">
          <Pulse className="h-5 w-36" />
          <Pulse className="h-3 w-64" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <Pulse className="size-8 flex-none rounded-xl" />
            <div className="flex-1 space-y-2">
              <Pulse className="h-3 w-3/4" />
              <Pulse className="h-3 w-1/2" />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export function ChartSkeleton() {
  const bars = [40, 65, 30, 80, 55, 70, 45]
  return (
    <Card>
      <CardHeader>
        <div className="space-y-2">
          <Pulse className="h-5 w-40" />
          <Pulse className="h-3 w-56" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex h-48 items-end gap-3">
          {bars.map((h, i) => (
            <Pulse key={i} className="flex-1" style={{ height: `${h}%` }} />
          ))}
        </div>
        <div className="mt-4 flex justify-between">
          {bars.map((_, i) => (
            <Pulse key={i} className="h-3 w-8" />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function LoadingScreen({ message }: { message?: string }) {
  const { isTurkish } = useLanguage()
  const resolved = message || (isTurkish ? 'Calisma alani yukleniyor' : 'Loading workspace')

  return (
    <div className="app-shell-grid flex min-h-screen items-center justify-center px-6">
      <div className="rounded-[32px] border border-[var(--line-soft)] bg-[var(--surface)] px-8 py-7 shadow-[var(--shadow-panel)]">
        <div className="flex items-center gap-4">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-[var(--primary-soft)]">
            <LoaderCircle className="size-5 animate-spin text-[var(--primary)]" />
          </div>
          <div>
            <p className="text-sm font-semibold text-[var(--text-strong)]">BADHABINOT</p>
            <p className="text-sm text-[var(--text-muted)]">{resolved}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
