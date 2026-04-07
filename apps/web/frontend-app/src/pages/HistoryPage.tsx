import { useMemo, useState } from 'react'
import { format, subDays } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { BarChart3, BellRing, Droplets } from 'lucide-react'
import { monitoringApi } from '@/api/monitoring'
import { ActivityFeedCard } from '@/features/dashboard/components/ActivityFeedCard'
import { BehaviorEventListCard } from '@/features/history/components/BehaviorEventListCard'
import { WeeklyTrendChart } from '@/features/history/components/WeeklyTrendChart'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { LoadingCard } from '@/components/ui/loading-state'
import { useLanguage } from '@/i18n/language-provider'

function SummaryCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof BarChart3
  label: string
  value: number
  detail: string
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-[var(--text-muted)]">{label}</p>
            <p className="mt-4 text-3xl font-extrabold tracking-tight text-white">{value}</p>
            <p className="mt-3 text-sm text-[var(--text-muted)]">{detail}</p>
          </div>
          <div className="flex size-12 items-center justify-center rounded-2xl bg-[rgba(255,255,255,0.06)]">
            <Icon className="size-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function HistoryPage() {
  const { isTurkish } = useLanguage()
  const [from, setFrom] = useState(format(subDays(new Date(), 6), 'yyyy-MM-dd'))

  const weeklyTrendQuery = useQuery({
    queryKey: ['weekly-trend', from],
    queryFn: () => monitoringApi.getWeeklyTrend(from),
  })

  const activitiesQuery = useQuery({
    queryKey: ['activities', 25],
    queryFn: () => monitoringApi.getActivities(25),
  })

  const eventsQuery = useQuery({
    queryKey: ['behavior-events', 20],
    queryFn: () => monitoringApi.getEvents(20),
  })

  const totals = useMemo(() => {
    const points = weeklyTrendQuery.data?.points ?? []
    return points.reduce(
      (accumulator, point) => ({
        alerts: accumulator.alerts + point.alert_count,
        reminders: accumulator.reminders + point.reminder_count,
        hydration: accumulator.hydration + point.hydration_count,
      }),
      { alerts: 0, reminders: 0, hydration: 0 },
    )
  }, [weeklyTrendQuery.data?.points])

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-[var(--text-muted)]">{isTurkish ? 'Secilen donem' : 'Selected period'}</p>
            <p className="mt-2 text-xl font-bold text-white">{isTurkish ? 'Yedi gunluk performans penceresi' : 'Seven-day performance window'}</p>
            <p className="mt-2 text-sm text-[var(--text-muted)]">
              {isTurkish
                ? 'Trend grafigi ve ozet metrikleri icin rapor penceresinin ilk gununu sec.'
                : 'Choose the first day of the reporting window used for the trend chart and summary metrics.'}
            </p>
          </div>
          <div className="w-full max-w-xs">
            <Input label={isTurkish ? 'Baslangic tarihi' : 'Start date'} type="date" value={from} onChange={(event) => setFrom(event.target.value)} />
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard
          icon={BellRing}
          label={isTurkish ? 'Uyarilar' : 'Alerts'}
          value={totals.alerts}
          detail={isTurkish ? 'Secilen haftadaki davranis ve durus uyarilari.' : 'Behavior and posture warnings in the selected week.'}
        />
        <SummaryCard
          icon={BarChart3}
          label={isTurkish ? 'Hatirlaticilar' : 'Reminders'}
          value={totals.reminders}
          detail={
            isTurkish
              ? 'Bu haftada kaydedilen manuel veya zamanli hatirlatici olaylari.'
              : 'Reminder events, manual or scheduled, recorded this week.'
          }
        />
        <SummaryCard
          icon={Droplets}
          label={isTurkish ? 'Su kayitlari' : 'Hydration logs'}
          value={totals.hydration}
          detail={isTurkish ? 'Ayni donem icin yakalanan su tuketim kayitlari.' : 'Water intake records captured for the same period.'}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
        {weeklyTrendQuery.isLoading ? (
          <LoadingCard message={isTurkish ? 'Haftalik trend yukleniyor' : 'Loading weekly trend'} />
        ) : (
          <WeeklyTrendChart points={weeklyTrendQuery.data?.points ?? []} />
        )}
        {eventsQuery.isLoading ? (
          <LoadingCard message={isTurkish ? 'Davranis olaylari yukleniyor' : 'Loading behavior events'} />
        ) : (
          <BehaviorEventListCard
            title={isTurkish ? 'Davranis olay akisi' : 'Behavior event stream'}
            description={
              isTurkish
                ? 'Izleme servisi tarafinda kaydedilen normalize durus, el hareketi ve sigara benzeri tespitler.'
                : 'Normalized posture, hand-movement, and smoking-like detections recorded by the monitoring service.'
            }
            events={eventsQuery.data ?? []}
          />
        )}
      </div>

      {activitiesQuery.isLoading ? (
        <LoadingCard message={isTurkish ? 'Aktivite gecmisi yukleniyor' : 'Loading activity history'} />
      ) : (
        <ActivityFeedCard
          title={isTurkish ? 'Ayrintili zaman cizelgesi' : 'Detailed timeline'}
          description={
            isTurkish
              ? 'Uyari, hatirlatici ve manuel islemlerdeki son zaman cizelgesi kayitlari.'
              : 'Recent timeline entries across alerts, reminders, and manual actions.'
          }
          items={activitiesQuery.data ?? []}
        />
      )}
    </div>
  )
}
