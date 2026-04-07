import { Activity, Lock, ScanSearch, ShieldCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useLanguage } from '@/i18n/language-provider'
import { behaviorLabel, postureLabel, toPercent } from '@/lib/format'
import type { AnalyzeFrameResponse, DashboardResponse } from '@/types/monitoring'

type InsightPanelProps = {
  dashboard: DashboardResponse
  latestAnalysis: AnalyzeFrameResponse | null
}

export function InsightPanel({ dashboard, latestAnalysis }: InsightPanelProps) {
  const { language, isTurkish } = useLanguage()
  const scores = latestAnalysis?.processing.scores ?? {}

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>{isTurkish ? 'Cikarim goruntusu' : 'Inference snapshot'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Duzenlenen goruntu-den-AI analiz hattindan donen son durus ve davranis sonucu.'
              : 'Latest posture and behavior result returned by the repaired vision-to-AI analysis pipeline.'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <Activity className="size-4" />
              {isTurkish ? 'Durus durumu' : 'Posture state'}
            </div>
            <p className="mt-3 text-xl font-bold text-white">{postureLabel(latestAnalysis?.posture_state, language)}</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <ScanSearch className="size-4" />
              {isTurkish ? 'Davranis' : 'Behavior'}
            </div>
            <p className="mt-3 text-xl font-bold text-white">{behaviorLabel(latestAnalysis?.behavior_type, language)}</p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">{isTurkish ? 'Guven' : 'Confidence'}</p>
            <p className="mt-3 text-2xl font-bold text-white">{toPercent(latestAnalysis?.confidence)}</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">{isTurkish ? 'Goruntu gecikmesi' : 'Vision latency'}</p>
            <p className="mt-3 text-2xl font-bold text-white">{latestAnalysis?.processing.vision_latency_ms ?? 0} ms</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">{isTurkish ? 'AI gecikmesi' : 'AI latency'}</p>
            <p className="mt-3 text-2xl font-bold text-white">{latestAnalysis?.processing.ai_latency_ms ?? 0} ms</p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">{isTurkish ? 'Ozet' : 'Summary'}</p>
            <p className="mt-3 text-sm leading-6 text-white">
              {latestAnalysis?.summary ?? (isTurkish ? 'Son ozeti doldurmak icin analiz calistir.' : 'Run an analysis to populate the latest summary.')}
            </p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">{isTurkish ? 'Oneri' : 'Recommendation'}</p>
            <p className="mt-3 text-sm leading-6 text-white">
              {latestAnalysis?.recommendation ??
                (isTurkish
                  ? 'Bir sonraki tamamlanan analizden sonra yonlendirme burada gorunecek.'
                  : 'Action guidance will appear here after the next completed analysis.')}
            </p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <ShieldCheck className="size-4" />
              {isTurkish ? 'Gizlilik modu' : 'Privacy mode'}
            </div>
            <p className="mt-3 text-sm font-semibold text-white">{dashboard.privacy_mode.replace(/_/g, ' ')}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
              {isTurkish
                ? 'Kareler sadece anlik orkestrasyon icin kullanilir ve arka uc tarafinda gorsel blob olarak saklanmaz.'
                : 'Frames are used only for immediate orchestration and are not persisted as image blobs by the backend.'}
            </p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <Lock className="size-4" />
              {isTurkish ? 'Model modu' : 'Model mode'}
            </div>
            <p className="mt-3 text-sm font-semibold text-white">{dashboard.model_mode}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
              {latestAnalysis?.model
                ? `${isTurkish ? 'Saglayici' : 'Provider'} ${latestAnalysis.model.provider} / ${latestAnalysis.model.name}`
                : isTurkish
                  ? 'Ust seviye analiz harici AI bagdastirici servisine yonlendirilir.'
                  : 'Higher-level analysis is routed through the external AI adapter service.'}
            </p>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-white">{isTurkish ? 'Model skorlari' : 'Model scores'}</p>
            <Badge variant="primary">{isTurkish ? 'Canli' : 'Live'}</Badge>
          </div>
          {Object.keys(scores).length === 0 ? (
            <p className="text-sm text-[var(--text-muted)]">
              {isTurkish ? 'Son skor dagilimini incelemek icin analiz calistir.' : 'Run an analysis to inspect the latest score breakdown.'}
            </p>
          ) : (
            <div className="space-y-3">
              {Object.entries(scores).map(([key, value]) => (
                <div key={key} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[var(--text-muted)]">{behaviorLabel(key, language)}</span>
                    <span className="font-semibold text-white">{toPercent(value)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-[rgba(255,255,255,0.06)]">
                    <div className="h-2 rounded-full bg-[linear-gradient(90deg,var(--primary),var(--accent))]" style={{ width: `${Math.max(value * 100, 6)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-white">{isTurkish ? 'Tespit edilen olaylar' : 'Detected events'}</p>
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
              {isTurkish
                ? 'Son analizde yuksek guvenli davranis olayi kaydedilmedi.'
                : 'No high-confidence behavior events were recorded in the latest analysis.'}
            </p>
          )}
        </div>

        {latestAnalysis?.generated_reminders.length ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-white">{isTurkish ? 'Uretilen hatirlaticilar' : 'Generated reminders'}</p>
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
