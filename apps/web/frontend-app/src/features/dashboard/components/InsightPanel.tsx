import { Activity, Lock, ScanSearch, ShieldCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { behaviorLabel, postureLabel, toPercent } from '@/lib/format'
import type { AnalyzeFrameResponse, DashboardResponse } from '@/types/monitoring'

type InsightPanelProps = {
  dashboard: DashboardResponse
  latestAnalysis: AnalyzeFrameResponse | null
}

export function InsightPanel({ dashboard, latestAnalysis }: InsightPanelProps) {
  const scores = latestAnalysis?.processing.scores ?? {}

  return (
    <Card className="h-full">
      <CardHeader>
        <div>
          <CardTitle>Inference snapshot</CardTitle>
          <CardDescription className="mt-2">Latest posture and behavior classification returned by the live analysis pipeline.</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <Activity className="size-4" />
              Posture state
            </div>
            <p className="mt-3 text-xl font-bold text-white">{postureLabel(latestAnalysis?.posture_state)}</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <ScanSearch className="size-4" />
              Behavior
            </div>
            <p className="mt-3 text-xl font-bold text-white">{behaviorLabel(latestAnalysis?.behavior_type)}</p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">Confidence</p>
            <p className="mt-3 text-2xl font-bold text-white">{toPercent(latestAnalysis?.confidence)}</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">Vision latency</p>
            <p className="mt-3 text-2xl font-bold text-white">{latestAnalysis?.processing.vision_latency_ms ?? 0} ms</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">AI latency</p>
            <p className="mt-3 text-2xl font-bold text-white">{latestAnalysis?.processing.ai_latency_ms ?? 0} ms</p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <ShieldCheck className="size-4" />
              Privacy mode
            </div>
            <p className="mt-3 text-sm font-semibold text-white">{dashboard.privacy_mode.replace(/_/g, ' ')}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">Frames are used only for immediate inference and not stored by the backend.</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <Lock className="size-4" />
              Model mode
            </div>
            <p className="mt-3 text-sm font-semibold text-white">{dashboard.model_mode}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">Switch between local and API-backed execution in settings if consent allows it.</p>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-white">Model scores</p>
            <Badge variant="primary">Live</Badge>
          </div>
          {Object.keys(scores).length === 0 ? (
            <p className="text-sm text-[var(--text-muted)]">Run an analysis to inspect the latest score breakdown.</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(scores).map(([key, value]) => (
                <div key={key} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-[var(--text-muted)]">{behaviorLabel(key)}</span>
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
      </CardContent>
    </Card>
  )
}

