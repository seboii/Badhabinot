import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Droplets, Flame, ShieldAlert, Waves } from 'lucide-react'
import { toast } from 'sonner'
import { monitoringApi } from '@/api/monitoring'
import { toErrorMessage } from '@/api/client'
import { ActivityFeedCard } from '@/features/dashboard/components/ActivityFeedCard'
import { InsightPanel } from '@/features/dashboard/components/InsightPanel'
import { LiveMonitorPanel } from '@/features/dashboard/components/LiveMonitorPanel'
import { QuickActionsCard } from '@/features/dashboard/components/QuickActionsCard'
import { BehaviorEventListCard } from '@/features/history/components/BehaviorEventListCard'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { LoadingCard } from '@/components/ui/loading-state'
import { useCamera } from '@/hooks/use-camera'
import { useLanguage } from '@/i18n/language-provider'
import { behaviorLabel, formatMilliliters, postureLabel } from '@/lib/format'
import type { AnalyzeFrameResponse } from '@/types/monitoring'

function MetricCard({
  title,
  value,
  detail,
  icon: Icon,
  accent,
}: {
  title: string
  value: string
  detail: string
  icon: typeof Waves
  accent: string
}) {
  return (
    <Card className="h-full">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-[var(--text-muted)]">{title}</p>
            <p className="mt-4 text-3xl font-extrabold tracking-tight text-white">{value}</p>
            <p className="mt-3 text-sm text-[var(--text-muted)]">{detail}</p>
          </div>
          <div className="flex size-12 items-center justify-center rounded-2xl" style={{ background: accent }}>
            <Icon className="size-5 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function DashboardPage() {
  const { language, isTurkish } = useLanguage()
  const queryClient = useQueryClient()
  const { videoRef, permissionState, errorMessage, streamReady, requestCamera, stopCamera, captureFrame } = useCamera()
  const [latestAnalysis, setLatestAnalysis] = useState<AnalyzeFrameResponse | null>(null)
  const [autoScan, setAutoScan] = useState(true)
  const [pendingAction, setPendingAction] = useState<'water' | 'water_reminder' | 'break' | undefined>(undefined)
  const inFlightRef = useRef(false)

  const dashboardQuery = useQuery({
    queryKey: ['dashboard'],
    queryFn: monitoringApi.getDashboard,
    refetchInterval: (query) => (query.state.data?.monitoring_active ? 15_000 : false),
  })

  const activitiesQuery = useQuery({
    queryKey: ['activities', 12],
    queryFn: () => monitoringApi.getActivities(12),
  })

  const eventsQuery = useQuery({
    queryKey: ['behavior-events', 8],
    queryFn: () => monitoringApi.getEvents(8),
  })

  const startSessionMutation = useMutation({
    mutationFn: () =>
      monitoringApi.startSession({
        client_surface: 'web',
        device_type: /mobile/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
      }),
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      toast.success(isTurkish ? 'Izleme oturumu baslatildi.' : 'Monitoring session started.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Izleme oturumu baslatilamadi.' : 'Unable to start the monitoring session.'))
    },
  })

  const stopSessionMutation = useMutation({
    mutationFn: (sessionId: string) => monitoringApi.stopSession(sessionId),
    onSuccess() {
      stopCamera()
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      toast.success(isTurkish ? 'Izleme oturumu durduruldu.' : 'Monitoring session stopped.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Izleme oturumu durdurulamadi.' : 'Unable to stop the monitoring session.'))
    },
  })

  const analyzeMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const frame = captureFrame()
      if (!frame) {
        throw new Error(isTurkish ? 'Kamera karesi henuz kullanilabilir degil.' : 'Camera frame is not available yet.')
      }

      return monitoringApi.analyze({
        session_id: sessionId,
        frame_id: `web-${Date.now()}`,
        captured_at: new Date().toISOString(),
        image_base64: frame.image_base64,
        image_content_type: frame.image_content_type,
      })
    },
    onSuccess(result) {
      setLatestAnalysis(result)
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      void queryClient.invalidateQueries({ queryKey: ['behavior-events'] })

      const detections = []
      result.events.forEach((event) => detections.push(behaviorLabel(event.event_type, language)))
      if (result.posture_state) {
        detections.push(postureLabel(result.posture_state, language))
      }

      toast.success(
        detections.length > 0
          ? isTurkish
            ? `Analiz guncellendi: ${detections.join(' / ')}`
            : `Analysis updated: ${detections.join(' / ')}`
          : isTurkish
            ? 'Analiz tamamlandi.'
            : 'Analysis completed.',
      )
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Mevcut kare analiz edilemedi.' : 'Unable to analyze the current frame.'))
    },
    onSettled() {
      inFlightRef.current = false
    },
  })

  const logHydrationMutation = useMutation({
    mutationFn: async () => {
      setPendingAction('water')
      return monitoringApi.logHydration({
        amount_ml: 250,
        source: 'manual',
        session_id: dashboardQuery.data?.active_session_id || undefined,
      })
    },
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      void queryClient.invalidateQueries({ queryKey: ['weekly-trend'] })
      toast.success(isTurkish ? 'Su kaydi eklendi.' : 'Hydration logged.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Su kaydi eklenemedi.' : 'Unable to log hydration.'))
    },
    onSettled() {
      setPendingAction(undefined)
    },
  })

  const waterReminderMutation = useMutation({
    mutationFn: async () => {
      setPendingAction('water_reminder')
      return monitoringApi.triggerReminder({
        reminder_type: 'water_reminder',
        message: isTurkish ? 'Bir bardak su zamani.' : 'Time for a glass of water.',
        session_id: dashboardQuery.data?.active_session_id || undefined,
      })
    },
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      void queryClient.invalidateQueries({ queryKey: ['weekly-trend'] })
      toast.success(isTurkish ? 'Su hatirlaticisi tetiklendi.' : 'Water reminder triggered.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Su hatirlaticisi tetiklenemedi.' : 'Unable to trigger the water reminder.'))
    },
    onSettled() {
      setPendingAction(undefined)
    },
  })

  const breakReminderMutation = useMutation({
    mutationFn: async () => {
      setPendingAction('break')
      return monitoringApi.triggerReminder({
        reminder_type: 'break_reminder',
        message: isTurkish ? 'Ayaga kalkip kisa bir esneme yap.' : 'Stand up and stretch for a moment.',
        session_id: dashboardQuery.data?.active_session_id || undefined,
      })
    },
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      void queryClient.invalidateQueries({ queryKey: ['weekly-trend'] })
      toast.success(isTurkish ? 'Mola hatirlaticisi tetiklendi.' : 'Break reminder triggered.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Mola hatirlaticisi tetiklenemedi.' : 'Unable to trigger the break reminder.'))
    },
    onSettled() {
      setPendingAction(undefined)
    },
  })

  const handleAnalyze = () => {
    const sessionId = dashboardQuery.data?.active_session_id

    if (!sessionId || !dashboardQuery.data?.monitoring_active) {
      toast.error(isTurkish ? 'Analizden once bir izleme oturumu baslat.' : 'Start a monitoring session before running analysis.')
      return
    }

    if (!dashboardQuery.data?.analysis_enabled) {
      toast.error(
        isTurkish
          ? 'Kareleri analiz etmeden once kamera ve uzak cikarim onayini etkinlestir.'
          : 'Enable camera and remote inference consent before analyzing frames.',
      )
      return
    }

    if (!streamReady) {
      toast.error(
        isTurkish
          ? 'Kamera akisi cevrimdisi. Kamera erisimi verip tekrar dene.'
          : 'Camera stream is offline. Grant camera access and retry.',
      )
      return
    }

    inFlightRef.current = true
    analyzeMutation.mutate(sessionId)
  }

  const handleStartMonitoring = async () => {
    if (dashboardQuery.data?.monitoring_active && dashboardQuery.data.active_session_id) {
      toast.info(
        isTurkish
          ? 'Bir izleme oturumu zaten aktif. Kamerayi yeniden bagla veya mevcut oturumu durdur.'
          : 'A monitoring session is already active. Reconnect camera or stop the existing session.',
      )
      return
    }

    if (!streamReady) {
      const granted = await requestCamera()
      if (!granted) {
        return
      }
    }

    startSessionMutation.mutate()
  }

  useEffect(() => {
    const sessionLive = Boolean(dashboardQuery.data?.monitoring_active && dashboardQuery.data?.active_session_id && streamReady)
    if (!sessionLive || !autoScan || analyzeMutation.isPending) {
      return
    }

    const sessionId = dashboardQuery.data?.active_session_id
    if (!sessionId) {
      return
    }

    const interval = window.setInterval(() => {
      if (inFlightRef.current) {
        return
      }

      inFlightRef.current = true
      analyzeMutation.mutate(sessionId)
    }, 12_000)

    return () => window.clearInterval(interval)
  }, [analyzeMutation, autoScan, dashboardQuery.data?.active_session_id, dashboardQuery.data?.monitoring_active, streamReady])

  const dashboard = dashboardQuery.data
  const activities = activitiesQuery.data ?? dashboard?.recent_activities ?? []
  const sessionActive = Boolean(dashboard?.monitoring_active && dashboard?.active_session_id)
  const monitoringLive = sessionActive && streamReady

  const waterProgress = useMemo(() => {
    if (!dashboard || dashboard.water_goal_ml === 0) {
      return 0
    }

    return Math.min((dashboard.water_progress_ml / dashboard.water_goal_ml) * 100, 100)
  }, [dashboard])

  if (dashboardQuery.isLoading || !dashboard) {
    return <LoadingCard message={isTurkish ? 'Canli panel yukleniyor' : 'Loading live dashboard'} />
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(360px,0.9fr)]">
        <LiveMonitorPanel
          videoRef={videoRef}
          monitoringLive={monitoringLive}
          sessionActive={sessionActive}
          activeSessionId={dashboard.active_session_id}
          analysisEnabled={dashboard.analysis_enabled}
          permissionState={permissionState}
          streamReady={streamReady}
          cameraError={errorMessage}
          autoScan={autoScan}
          latestAnalysis={latestAnalysis}
          isStarting={startSessionMutation.isPending}
          isStopping={stopSessionMutation.isPending}
          isAnalyzing={analyzeMutation.isPending}
          onRequestCamera={requestCamera}
          onStartMonitoring={handleStartMonitoring}
          onStopMonitoring={() => dashboard.active_session_id && stopSessionMutation.mutate(dashboard.active_session_id)}
          onAnalyzeNow={handleAnalyze}
          onToggleAutoScan={setAutoScan}
        />
        <InsightPanel dashboard={dashboard} latestAnalysis={latestAnalysis} />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title={isTurkish ? 'Seri' : 'Streak'}
          value={`${dashboard.streak_days}`}
          detail={
            isTurkish
              ? 'Izleme veya su kaydi ile ard arda aktif gunler.'
              : 'Consecutive active days with monitoring or hydration logs.'
          }
          icon={Flame}
          accent="rgba(217, 70, 239, 0.18)"
        />
        <MetricCard
          title={isTurkish ? 'Bugunku uyarilar' : 'Alerts today'}
          value={`${dashboard.alert_count_today}`}
          detail={
            isTurkish
              ? 'Bugun basindan beri kaydedilen davranis ve durus uyarilari.'
              : 'Behavior and posture alerts recorded since the start of today.'
          }
          icon={ShieldAlert}
          accent="rgba(251, 113, 133, 0.18)"
        />
        <MetricCard
          title={isTurkish ? 'Bugunku hatirlaticilar' : 'Reminders today'}
          value={`${dashboard.reminder_count_today}`}
          detail={
            isTurkish
              ? 'Izleme servisinin kaydettigi manuel ve zamanli hatirlatici etkinligi.'
              : 'Manual and scheduled reminder activity logged by the monitoring service.'
          }
          icon={Waves}
          accent="rgba(139, 92, 246, 0.18)"
        />
        <Card>
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-[var(--text-muted)]">{isTurkish ? 'Su hedefi' : 'Water goal'}</p>
                <p className="mt-4 text-3xl font-extrabold tracking-tight text-white">{formatMilliliters(dashboard.water_progress_ml, language)}</p>
                <p className="mt-3 text-sm text-[var(--text-muted)]">
                  {isTurkish ? 'Hedef' : 'Target'} {formatMilliliters(dashboard.water_goal_ml, language)}
                </p>
              </div>
              <div className="flex size-12 items-center justify-center rounded-2xl bg-[rgba(96,165,250,0.18)]">
                <Droplets className="size-5 text-white" />
              </div>
            </div>
            <div className="mt-5 h-2 rounded-full bg-[var(--surface-muted)]">
              <div className="h-2 rounded-full bg-[linear-gradient(90deg,var(--info),var(--primary))]" style={{ width: `${waterProgress}%` }} />
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-[var(--text-muted)]">
              <span>{Math.round(waterProgress)}% {isTurkish ? 'tamamlandi' : 'completed'}</span>
              <Badge variant="info">{isTurkish ? 'Su takibi' : 'Hydration'}</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
        {activitiesQuery.isLoading ? (
          <LoadingCard message={isTurkish ? 'Son aktiviteler yukleniyor' : 'Loading recent activities'} />
        ) : (
          <ActivityFeedCard
            title={isTurkish ? 'Son aktivite' : 'Recent activity'}
            description={
              isTurkish
                ? 'Izleme-servisi tarafinda kaydedilen uyarilar, hatirlaticilar ve manuel islemler.'
                : 'Alerts, reminders, and manual actions persisted by monitoring-service.'
            }
            items={activities}
          />
        )}

        <QuickActionsCard
          onLogWater={() => logHydrationMutation.mutate()}
          onWaterReminder={() => waterReminderMutation.mutate()}
          onBreakReminder={() => breakReminderMutation.mutate()}
          pendingAction={pendingAction}
        />
      </div>

      {eventsQuery.isLoading ? (
        <LoadingCard message={isTurkish ? 'Son davranis olaylari yukleniyor' : 'Loading recent behavior events'} />
      ) : (
        <BehaviorEventListCard
          title={isTurkish ? 'Davranis olaylari' : 'Behavior events'}
          description={
            isTurkish
              ? 'Raporlama, hatirlatici ve veriye dayali sohbet icin kaydedilen normalize tespitler.'
              : 'Normalized detections persisted for reporting, reminders, and grounded chat.'
          }
          events={eventsQuery.data ?? []}
        />
      )}
    </div>
  )
}
