import { Activity, Eye, ScanSearch, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useLanguage } from '@/i18n/language-provider'
import { behaviorLabel, postureLabel } from '@/lib/format'
import type { AnalyzeFrameResponse } from '@/types/monitoring'

type InsightPanelProps = {
  latestAnalysis: AnalyzeFrameResponse | null
}

const BEHAVIOR_EMOJI: Record<string, string> = {
  SMOKING: '🚬',
  EATING: '🍽️',
  DRINKING: '🥤',
  SLOUCHING: '🪑',
  FACE_TOUCH: '✋',
  LEFT_SCREEN: '👁️',
  DROWSY: '😴',
  YAWNING: '🥱',
  DISTRACTED: '👀',
  GAZE_AWAY: '👀',
  STRANGER_DETECTED: '👤',
  OWNER_ABSENT: '🔴',
  UNKNOWN_PERSON: '❓',
  HAND_MOVEMENT: '🖐️',
}

function postureColor(state: string | null | undefined): string {
  switch ((state || '').toLowerCase()) {
    case 'good':
      return 'text-[var(--success)]'
    case 'poor':
      return 'text-[var(--danger)]'
    default:
      return 'text-white'
  }
}

export function InsightPanel({ latestAnalysis }: InsightPanelProps) {
  const { language, isTurkish } = useLanguage()

  const visionEvents = latestAnalysis?.vision_behavior_events ?? []

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>{isTurkish ? 'Canlı Analiz' : 'Live Analysis'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Kameradan anlık tespitler ve öneriler.'
              : 'Real-time detections and guidance.'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">

        {/* ── Anlık tespit ───────────────────────────────────── */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="flex items-center gap-2 text-sm font-semibold text-white">
              <Zap className="size-4 text-yellow-400" />
              {isTurkish ? 'Anlık Tespit' : 'Live Detection'}
            </p>
            <Badge variant={visionEvents.length > 0 ? 'warning' : 'info'}>
              {visionEvents.length > 0
                ? `${visionEvents.length} ${isTurkish ? 'tespit' : 'detected'}`
                : isTurkish ? 'Temiz' : 'Clear'}
            </Badge>
          </div>

          {visionEvents.length > 0 ? (
            <div className="space-y-2">
              {visionEvents.map((ev, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-[16px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.04)] px-4 py-3"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-base">{BEHAVIOR_EMOJI[ev.event_type.toUpperCase()] ?? '⚡'}</span>
                    <p className="text-sm font-semibold text-white">{behaviorLabel(ev.event_type, language)}</p>
                  </div>
                  <Badge variant={ev.severity === 'high' ? 'danger' : ev.severity === 'medium' ? 'warning' : 'info'}>
                    {ev.severity}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-[16px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.02)] px-4 py-3">
              <p className="text-sm text-[var(--text-muted)]">
                {latestAnalysis
                  ? isTurkish
                    ? 'Bu karede anormal davranış tespit edilmedi.'
                    : 'No abnormal behavior detected in this frame.'
                  : isTurkish
                    ? 'İzleme başlatıldığında tespitler burada görünür.'
                    : 'Detections will appear here once monitoring starts.'}
              </p>
            </div>
          )}
        </div>

        {/* ── Duruş + Davranış ──────────────────────────────── */}
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <Activity className="size-4" />
              {isTurkish ? 'Duruş durumu' : 'Posture state'}
            </div>
            <p className={`mt-3 text-xl font-bold ${postureColor(latestAnalysis?.posture_state)}`}>
              {postureLabel(latestAnalysis?.posture_state, language)}
            </p>
            {latestAnalysis?.posture_reason ? (
              <p className="mt-2 text-xs leading-5 text-[var(--text-muted)]">{latestAnalysis.posture_reason}</p>
            ) : null}
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <ScanSearch className="size-4" />
              {isTurkish ? 'Davranış' : 'Behavior'}
            </div>
            <p className="mt-3 text-xl font-bold text-white">{behaviorLabel(latestAnalysis?.behavior_type, language)}</p>
          </div>
        </div>

        {/* ── Özet + Öneri ──────────────────────────────────── */}
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.14em] text-[var(--text-soft)]">{isTurkish ? 'Özet' : 'Summary'}</p>
            <p className="mt-3 text-sm leading-6 text-white">
              {latestAnalysis?.summary ?? (isTurkish ? 'Analiz başlatıldığında özet burada görünür.' : 'Run an analysis to populate the latest summary.')}
            </p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.14em] text-[var(--text-soft)]">{isTurkish ? 'Öneri' : 'Recommendation'}</p>
            <p className="mt-3 text-sm leading-6 text-white">
              {latestAnalysis?.recommendation ?? (isTurkish ? 'Öneri bir sonraki analizden sonra görünür.' : 'Action guidance will appear after the next analysis.')}
            </p>
          </div>
        </div>

        {/* ── Kaydedilen olaylar ────────────────────────────── */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-white">{isTurkish ? 'Kaydedilen Olaylar' : 'Recorded Events'}</p>
            <Badge variant="info">{latestAnalysis?.events.length ?? 0}</Badge>
          </div>
          {latestAnalysis?.events.length ? (
            <div className="space-y-3">
              {latestAnalysis.events.map((event) => (
                <div key={event.event_id} className="rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-white">{behaviorLabel(event.event_type, language)}</p>
                    <Badge variant={event.severity === 'high' ? 'danger' : event.severity === 'medium' ? 'warning' : 'info'}>
                      {event.severity}
                    </Badge>
                  </div>
                  {event.interpretation ? (
                    <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{event.interpretation}</p>
                  ) : null}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)]">
              {isTurkish ? 'Son analizde önemli bir davranış olayı kaydedilmedi.' : 'No notable behavior events were recorded in the latest analysis.'}
            </p>
          )}
        </div>

        {/* ── Üretilen hatırlatıcılar ───────────────────────── */}
        {latestAnalysis?.generated_reminders.length ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="flex items-center gap-2 text-sm font-semibold text-white">
                <Eye className="size-4" />
                {isTurkish ? 'Hatırlatıcılar' : 'Reminders'}
              </p>
              <Badge variant="warning">{latestAnalysis.generated_reminders.length}</Badge>
            </div>
            {latestAnalysis.generated_reminders.map((reminder) => (
              <div key={reminder.reminder_id} className="rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                <p className="text-sm font-semibold text-white">{behaviorLabel(reminder.reminder_type, language)}</p>
                <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{reminder.message}</p>
              </div>
            ))}
          </div>
        ) : null}

        <p className="text-xs text-[var(--text-muted)]">
          {isTurkish ? '🔒 Kameranızdan alınan kareler saklanmaz.' : '🔒 Camera frames are not stored.'}
        </p>

      </CardContent>
    </Card>
  )
}
