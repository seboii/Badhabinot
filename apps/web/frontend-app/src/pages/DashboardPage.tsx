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
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { LoadingCard } from '@/components/ui/loading-state'
import { useCamera } from '@/hooks/use-camera'
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
  const queryClient = useQueryClient()
  const { videoRef, permissionState, errorMessage, streamReady, requestCamera, captureFrame } = useCamera()
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

  const startSessionMutation = useMutation({
    mutationFn: () =>
      monitoringApi.startSession({
        client_surface: 'web',
        device_type: /mobile/i.test(navigator.userAgent) ? 'mobile' : 'desktop',
      }),
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      toast.success('Monitoring session started.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to start the monitoring session.'))
    },
  })

  const stopSessionMutation = useMutation({
    mutationFn: (sessionId: string) => monitoringApi.stopSession(sessionId),
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      toast.success('Monitoring session stopped.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to stop the monitoring session.'))
    },
  })

  const analyzeMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      const frame = captureFrame()
      if (!frame) {
        throw new Error('Camera frame is not available yet.')
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

      const detections = []
      if (result.behavior_type && result.behavior_type !== 'none') {
        detections.push(behaviorLabel(result.behavior_type))
      }
      if (result.posture_state) {
        detections.push(postureLabel(result.posture_state))
      }

      toast.success(detections.length > 0 ? `Analysis updated: ${detections.join(' · ')}` : 'Analysis completed.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to analyze the current frame.'))
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
      toast.success('Hydration logged.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to log hydration.'))
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
        message: 'Time for a glass of water.',
        session_id: dashboardQuery.data?.active_session_id || undefined,
      })
    },
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      void queryClient.invalidateQueries({ queryKey: ['weekly-trend'] })
      toast.success('Water reminder triggered.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to trigger the water reminder.'))
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
        message: 'Stand up and stretch for a moment.',
        session_id: dashboardQuery.data?.active_session_id || undefined,
      })
    },
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      void queryClient.invalidateQueries({ queryKey: ['weekly-trend'] })
      toast.success('Break reminder triggered.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to trigger the break reminder.'))
    },
    onSettled() {
      setPendingAction(undefined)
    },
  })

  const handleAnalyze = () => {
    const sessionId = dashboardQuery.data?.active_session_id

    if (!sessionId) {
      toast.error('Start a monitoring session before running analysis.')
      return
    }

    if (!streamReady) {
      toast.error('Grant camera access before analyzing frames.')
      return
    }

    inFlightRef.current = true
    analyzeMutation.mutate(sessionId)
  }

  const handleStartMonitoring = async () => {
    if (!streamReady) {
      await requestCamera()
      return
    }

    startSessionMutation.mutate()
  }

  useEffect(() => {
    if (!dashboardQuery.data?.monitoring_active || !autoScan || !streamReady || analyzeMutation.isPending) {
      return
    }

    const sessionId = dashboardQuery.data.active_session_id
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

  const waterProgress = useMemo(() => {
    if (!dashboard || dashboard.water_goal_ml === 0) {
      return 0
    }

    return Math.min((dashboard.water_progress_ml / dashboard.water_goal_ml) * 100, 100)
  }, [dashboard])

  if (dashboardQuery.isLoading || !dashboard) {
    return <LoadingCard message="Loading live dashboard" />
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.7fr)_minmax(360px,0.9fr)]">
        <LiveMonitorPanel
          videoRef={videoRef}
          monitoringActive={dashboard.monitoring_active}
          activeSessionId={dashboard.active_session_id}
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
          title="Streak"
          value={`${dashboard.streak_days}`}
          detail="Consecutive active days with monitoring or hydration logs."
          icon={Flame}
          accent="rgba(217, 70, 239, 0.18)"
        />
        <MetricCard
          title="Alerts today"
          value={`${dashboard.alert_count_today}`}
          detail="Behavior and posture alerts recorded since the start of today."
          icon={ShieldAlert}
          accent="rgba(251, 113, 133, 0.18)"
        />
        <MetricCard
          title="Reminders today"
          value={`${dashboard.reminder_count_today}`}
          detail="Manual and scheduled reminder activity logged by the monitoring service."
          icon={Waves}
          accent="rgba(139, 92, 246, 0.18)"
        />
        <Card>
          <CardContent className="p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-[var(--text-muted)]">Water goal</p>
                <p className="mt-4 text-3xl font-extrabold tracking-tight text-white">{formatMilliliters(dashboard.water_progress_ml)}</p>
                <p className="mt-3 text-sm text-[var(--text-muted)]">Target {formatMilliliters(dashboard.water_goal_ml)}</p>
              </div>
              <div className="flex size-12 items-center justify-center rounded-2xl bg-[rgba(96,165,250,0.18)]">
                <Droplets className="size-5 text-white" />
              </div>
            </div>
            <div className="mt-5 h-2 rounded-full bg-[var(--surface-muted)]">
              <div className="h-2 rounded-full bg-[linear-gradient(90deg,var(--info),var(--primary))]" style={{ width: `${waterProgress}%` }} />
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-[var(--text-muted)]">
              <span>{Math.round(waterProgress)}% completed</span>
              <Badge variant="info">Hydration</Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
        {activitiesQuery.isLoading ? (
          <LoadingCard message="Loading recent activities" />
        ) : (
          <ActivityFeedCard
            title="Recent activity"
            description="Alerts, reminders, and manual actions persisted by monitoring-service."
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
    </div>
  )
}
