import { Activity, Eye, Lock, ScanSearch, ShieldCheck, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useLanguage } from '@/i18n/language-provider'
import { behaviorLabel, postureLabel, toPercent } from '@/lib/format'
import type { AnalyzeFrameResponse, DashboardResponse } from '@/types/monitoring'

type InsightPanelProps = {
  dashboard: DashboardResponse
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

function scoreBarColor(value: number): string {
  if (value >= 0.55) return 'linear-gradient(90deg,#ef4444,#f97316)'
  if (value >= 0.30) return 'linear-gradient(90deg,#f59e0b,#fb923c)'
  return 'linear-gradient(90deg,var(--primary),var(--accent))'
}

export function InsightPanel({ dashboard, latestAnalysis }: InsightPanelProps) {
  const { language, isTurkish } = useLanguage()

  const visionEvents = latestAnalysis?.vision_behavior_events ?? []
  const scores = latestAnalysis?.processing.scores ?? {}
  const visibleScores = Object.entries(scores).filter(([, v]) => v > 0.08)

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>{isTurkish ? 'Canlı Analiz' : 'Live Analysis'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'YOLOv8 + Vision servisten gelen anlık tespit ve AI analiz sonuçları.'
              : 'Real-time detections from YOLOv8 + Vision service and AI analysis results.'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">

        {/* ── YOLOv8 Canlı Tespit ───────────────────────────── */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="flex items-center gap-2 text-sm font-semibold text-white">
              <Zap className="size-4 text-yellow-400" />
              {isTurkish ? 'YOLOv8 Canlı Tespit' : 'YOLOv8 Live Detection'}
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
                    <div>
                      <p className="text-sm font-semibold text-white">{behaviorLabel(ev.event_type, language)}</p>
                      {ev.detail ? (
                        <p className="text-xs text-[var(--text-muted)]">{ev.detail}</p>
                      ) : null}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={ev.severity === 'high' ? 'danger' : ev.severity === 'medium' ? 'warning' : 'info'}>
                      {ev.severity}
                    </Badge>
                    <span className="text-xs text-[var(--text-muted)]">{Math.round(ev.confidence * 100)}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-[16px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.02)] px-4 py-3">
              <p className="text-sm text-[var(--text-muted)]">
                {latestAnalysis
                  ? isTurkish
                    ? 'YOLOv8 bu karede anormal davranış tespit etmedi.'
                    : 'YOLOv8 detected no abnormal behavior in this frame.'
                  : isTurkish
                    ? 'İzleme başlatıldığında YOLOv8 tespitleri burada görünür.'
                    : 'YOLOv8 detections will appear here once monitoring starts.'}
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
            <p className="mt-3 text-xl font-bold text-white">{postureLabel(latestAnalysis?.posture_state, language)}</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <ScanSearch className="size-4" />
              {isTurkish ? 'Davranış' : 'Behavior'}
            </div>
            <p className="mt-3 text-xl font-bold text-white">{behaviorLabel(latestAnalysis?.behavior_type, language)}</p>
          </div>
        </div>

        {/* ── Güven + Gecikme ───────────────────────────────── */}
        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.14em] text-[var(--text-soft)]">{isTurkish ? 'Güven' : 'Confidence'}</p>
            <p className="mt-3 text-2xl font-bold text-white">{toPercent(latestAnalysis?.confidence)}</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.14em] text-[var(--text-soft)]">{isTurkish ? 'Görüntü' : 'Vision'}</p>
            <p className="mt-3 text-2xl font-bold text-white">{latestAnalysis?.processing.vision_latency_ms ?? 0}ms</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.14em] text-[var(--text-soft)]">AI</p>
            <p className="mt-3 text-2xl font-bold text-white">{latestAnalysis?.processing.ai_latency_ms ?? 0}ms</p>
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

        {/* ── Model Skorları — geçiş animasyonlu + renkli ───── */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-white">{isTurkish ? 'Model Skorları' : 'Model Scores'}</p>
            <Badge variant="primary">{isTurkish ? 'Canlı' : 'Live'}</Badge>
          </div>
          {visibleScores.length === 0 ? (
            <p className="text-sm text-[var(--text-muted)]">
              {isTurkish ? 'Analiz başlatıldığında skor dağılımı burada görünür.' : 'Run an analysis to inspect the latest score breakdown.'}
            </p>
          ) : (
            <div className="space-y-3">
              {visibleScores.map(([key, value]) => (
                <div key={key} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[var(--text-muted)]">{behaviorLabel(key, language)}</span>
                    <span className="font-semibold text-white">{toPercent(value)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-[rgba(255,255,255,0.06)]">
                    <div
                      className="h-2 rounded-full"
                      style={{
                        width: `${Math.max(value * 100, 4)}%`,
                        background: scoreBarColor(value),
                        transition: 'width 0.7s ease-out',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Tespit Edilen Olaylar ─────────────────────────── */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-white">{isTurkish ? 'Kayıtlı Olaylar' : 'Recorded Events'}</p>
            <Badge variant="info">{latestAnalysis?.events.length ?? 0}</Badge>
          </div>
          {latestAnalysis?.events.length ? (
            <div className="space-y-3">
              {latestAnalysis.events.map((event) => (
                <div key={event.event_id} className="rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-white">{behaviorLabel(event.event_type, language)}</p>
                    <Badge variant={event.severity === 'high' ? 'danger' : event.severity === 'medium' ? 'warning' : 'info'}>
                      {Math.round(event.confidence * 100)}%
                    </Badge>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{event.interpretation}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)]">
              {isTurkish ? 'Son analizde yüksek güvenli davranış olayı kaydedilmedi.' : 'No high-confidence behavior events were recorded in the latest analysis.'}
            </p>
          )}
        </div>

        {/* ── Gizlilik + Model Modu ─────────────────────────── */}
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <ShieldCheck className="size-4" />
              {isTurkish ? 'Gizlilik' : 'Privacy'}
            </div>
            <p className="mt-3 text-sm font-semibold text-white">{dashboard.privacy_mode.replace(/_/g, ' ')}</p>
            <p className="mt-2 text-xs leading-5 text-[var(--text-muted)]">
              {isTurkish ? 'Kareler saklanmaz.' : 'Frames are not persisted.'}
            </p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <Lock className="size-4" />
              {isTurkish ? 'Model' : 'Model'}
            </div>
            <p className="mt-3 text-sm font-semibold text-white">{dashboard.model_mode}</p>
            <p className="mt-2 text-xs leading-5 text-[var(--text-muted)]">
              {latestAnalysis?.model
                ? `${latestAnalysis.model.provider} / ${latestAnalysis.model.name}`
                : isTurkish ? 'Analiz bekleniyor.' : 'Awaiting analysis.'}
            </p>
          </div>
        </div>

        {/* ── Üretilen Hatırlatıcılar ───────────────────────── */}
        {latestAnalysis?.generated_reminders.length ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="flex items-center gap-2 text-sm font-semibold text-white">
                <Eye className="size-4" />
                {isTurkish ? 'Üretilen Hatırlatıcılar' : 'Generated Reminders'}
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

      </CardContent>
    </Card>
  )
}
