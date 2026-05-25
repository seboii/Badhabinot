import { useMemo, useState } from 'react'
import { format, subDays } from 'date-fns'
import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { BarChart3, BellRing, Droplets } from 'lucide-react'
import { monitoringApi } from '@/api/monitoring'
import { ActivityFeedCard } from '@/features/dashboard/components/ActivityFeedCard'
import { BehaviorEventListCard } from '@/features/history/components/BehaviorEventListCard'
import { WeeklyTrendChart } from '@/features/history/components/WeeklyTrendChart'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ActivityFeedSkeleton, ChartSkeleton, MetricCardSkeleton } from '@/components/ui/loading-state'
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
            <p className="mt-4 text-2xl font-extrabold tracking-tight text-white sm:text-3xl">{value}</p>
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

  const PAGE_SIZE = 15

  const activitiesQuery = useInfiniteQuery({
    queryKey: ['activities'],
    queryFn: ({ pageParam }) => monitoringApi.getActivities(pageParam as number, PAGE_SIZE),
    initialPageParam: 0,
    getNextPageParam: (lastPage, _allPages, lastPageParam) =>
      lastPage.length === PAGE_SIZE ? (lastPageParam as number) + 1 : undefined,
  })

  const eventsQuery = useInfiniteQuery({
    queryKey: ['behavior-events'],
    queryFn: ({ pageParam }) => monitoringApi.getEvents(pageParam as number, PAGE_SIZE),
    initialPageParam: 0,
    getNextPageParam: (lastPage, _allPages, lastPageParam) =>
      lastPage.length === PAGE_SIZE ? (lastPageParam as number) + 1 : undefined,
  })

  const activitiesFlat = useMemo(() => activitiesQuery.data?.pages.flat() ?? [], [activitiesQuery.data])
  const eventsFlat = useMemo(() => eventsQuery.data?.pages.flat() ?? [], [eventsQuery.data])

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
        {weeklyTrendQuery.isLoading ? (
          <>
            <MetricCardSkeleton />
            <MetricCardSkeleton />
            <MetricCardSkeleton />
          </>
        ) : (
          <>
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
          </>
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
        {weeklyTrendQuery.isLoading ? (
          <ChartSkeleton />
        ) : (
          <WeeklyTrendChart points={weeklyTrendQuery.data?.points ?? []} />
        )}
        {eventsQuery.isLoading ? (
          <ActivityFeedSkeleton />
        ) : (
          <BehaviorEventListCard
            title={isTurkish ? 'Davranis olay akisi' : 'Behavior event stream'}
            description={
              isTurkish
                ? 'Izleme servisi tarafinda kaydedilen normalize durus, el hareketi ve sigara benzeri tespitler.'
                : 'Normalized posture, hand-movement, and smoking-like detections recorded by the monitoring service.'
            }
            events={eventsFlat}
            hasMore={eventsQuery.hasNextPage}
            isLoadingMore={eventsQuery.isFetchingNextPage}
            onLoadMore={() => void eventsQuery.fetchNextPage()}
          />
        )}
      </div>

      {activitiesQuery.isLoading ? (
        <ActivityFeedSkeleton />
      ) : (
        <ActivityFeedCard
          title={isTurkish ? 'Ayrintili zaman cizelgesi' : 'Detailed timeline'}
          description={
            isTurkish
              ? 'Uyari, hatirlatici ve manuel islemlerdeki son zaman cizelgesi kayitlari.'
              : 'Recent timeline entries across alerts, reminders, and manual actions.'
          }
          items={activitiesFlat}
          hasMore={activitiesQuery.hasNextPage}
          isLoadingMore={activitiesQuery.isFetchingNextPage}
          onLoadMore={() => void activitiesQuery.fetchNextPage()}
        />
      )}
    </div>
  )
}
