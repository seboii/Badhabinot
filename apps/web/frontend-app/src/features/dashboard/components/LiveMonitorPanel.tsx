import type { RefObject } from 'react'
import { Camera, Play, ScanFace, Square, VideoOff } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import type { AnalyzeFrameResponse } from '@/types/monitoring'

type LiveMonitorPanelProps = {
  videoRef: RefObject<HTMLVideoElement | null>
  monitoringActive: boolean
  activeSessionId: string | null
  permissionState: string
  streamReady: boolean
  cameraError: string | null
  autoScan: boolean
  latestAnalysis: AnalyzeFrameResponse | null
  isStarting: boolean
  isStopping: boolean
  isAnalyzing: boolean
  onRequestCamera: () => void
  onStartMonitoring: () => void
  onStopMonitoring: () => void
  onAnalyzeNow: () => void
  onToggleAutoScan: (checked: boolean) => void
}

export function LiveMonitorPanel({
  videoRef,
  monitoringActive,
  activeSessionId,
  permissionState,
  streamReady,
  cameraError,
  autoScan,
  latestAnalysis,
  isStarting,
  isStopping,
  isAnalyzing,
  onRequestCamera,
  onStartMonitoring,
  onStopMonitoring,
  onAnalyzeNow,
  onToggleAutoScan,
}: LiveMonitorPanelProps) {
  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <CardTitle>Live monitor</CardTitle>
            <Badge variant={monitoringActive ? 'success' : 'neutral'}>{monitoringActive ? 'ACTIVE' : 'IDLE'}</Badge>
            <Badge variant="primary">{permissionState.toUpperCase()}</Badge>
          </div>
          <CardDescription className="mt-2">
            Browser camera preview, session controls, and frame analysis aligned with the uploaded desktop dashboard design.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="relative overflow-hidden rounded-[28px] border border-[var(--line-soft)] bg-black">
          {streamReady ? (
            <>
              <video ref={videoRef} className="aspect-video w-full object-cover" muted playsInline />
              <div className="pointer-events-none absolute inset-x-0 top-0 h-0.5 bg-[var(--primary)] shadow-[0_0_24px_var(--primary)] animate-[pulse_2.6s_ease-in-out_infinite]" />
            </>
          ) : (
            <div className="flex aspect-video flex-col items-center justify-center gap-4 text-center">
              <div className="flex size-16 items-center justify-center rounded-3xl bg-[rgba(255,255,255,0.06)]">
                <VideoOff className="size-7 text-[var(--text-muted)]" />
              </div>
              <div className="space-y-2">
                <p className="text-base font-semibold text-white">Camera preview is offline</p>
                <p className="max-w-md text-sm leading-6 text-[var(--text-muted)]">
                  Grant browser camera permission to unlock live analysis and session-backed monitoring.
                </p>
              </div>
            </div>
          )}
        </div>

        {cameraError ? <p className="text-sm text-[var(--danger)]">{cameraError}</p> : null}

        <div className="flex flex-col gap-3 md:flex-row md:flex-wrap">
          <Button variant="secondary" iconLeft={<Camera className="size-4" />} onClick={onRequestCamera}>
            {streamReady ? 'Refresh camera' : 'Grant camera access'}
          </Button>

          {monitoringActive ? (
            <Button
              variant="danger"
              iconLeft={<Square className="size-4" />}
              loading={isStopping}
              onClick={onStopMonitoring}
            >
              Stop monitoring
            </Button>
          ) : (
            <Button
              variant="primary"
              iconLeft={<Play className="size-4" />}
              loading={isStarting}
              onClick={onStartMonitoring}
            >
              Start monitoring
            </Button>
          )}

          <Button
            variant="outline"
            iconLeft={<ScanFace className="size-4" />}
            loading={isAnalyzing}
            onClick={onAnalyzeNow}
            disabled={!monitoringActive || !streamReady}
          >
            Analyze now
          </Button>
        </div>

        <div className="grid gap-3 rounded-[28px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4 md:grid-cols-[1fr_auto] md:items-center">
          <div>
            <p className="text-sm font-semibold text-white">Continuous scan</p>
            <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">
              Poll the live feed every 12 seconds while the session is active.
            </p>
          </div>
          <Switch checked={autoScan} onCheckedChange={onToggleAutoScan} />
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">Session ID</p>
            <p className="mt-3 break-all text-sm font-semibold text-white">{activeSessionId ?? 'No active session'}</p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">Presence</p>
            <p className="mt-3 text-sm font-semibold text-white">
              {latestAnalysis ? (latestAnalysis.subject_present ? 'Detected in frame' : 'Not detected') : 'Awaiting analysis'}
            </p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">Frame status</p>
            <p className="mt-3 text-sm font-semibold text-white">{streamReady ? 'Live preview available' : 'Camera unavailable'}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

