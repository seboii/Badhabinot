import { useRef } from 'react'
import type { RefObject } from 'react'
import { Camera, Loader2, Play, ScanFace, Square, UserRound, VideoOff } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import type { CameraPermissionState } from '@/hooks/use-camera'
import { useMediaPipeLive } from '@/hooks/use-mediapipe-live'
import { useLanguage } from '@/i18n/language-provider'
import type { AnalyzeFrameResponse } from '@/types/monitoring'

type LiveMonitorPanelProps = {
  videoRef: RefObject<HTMLVideoElement | null>
  monitoringLive: boolean
  sessionActive: boolean
  activeSessionId: string | null
  analysisEnabled: boolean
  permissionState: CameraPermissionState
  streamReady: boolean
  cameraError: string | null
  autoScan: boolean
  latestAnalysis: AnalyzeFrameResponse | null
  isStarting: boolean
  isStopping: boolean
  isAnalyzing: boolean
  showOverlay: boolean
  isThrottled: boolean
  onRequestCamera: () => void
  onStartMonitoring: () => void
  onStopMonitoring: () => void
  onAnalyzeNow: () => void
  onToggleAutoScan: (checked: boolean) => void
  onToggleOverlay: (checked: boolean) => void
  onOpenFaceRegistration: () => void
}

export function LiveMonitorPanel({
  videoRef,
  monitoringLive,
  sessionActive,
  activeSessionId,
  analysisEnabled,
  permissionState,
  streamReady,
  cameraError,
  autoScan,
  latestAnalysis,
  isStarting,
  isStopping,
  isAnalyzing,
  showOverlay,
  isThrottled,
  onRequestCamera,
  onStartMonitoring,
  onStopMonitoring,
  onAnalyzeNow,
  onToggleAutoScan,
  onToggleOverlay,
  onOpenFaceRegistration,
}: LiveMonitorPanelProps) {
  const { isTurkish } = useLanguage()
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  // MediaPipe runs in the browser — face mesh + hand skeleton at ~30 fps.
  // Active only when the camera is live AND the overlay switch is on.
  const mpState = useMediaPipeLive(videoRef, canvasRef, monitoringLive && showOverlay)

  const canAnalyze = monitoringLive && streamReady && analysisEnabled
  const auth = latestAnalysis?.face_auth

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <CardTitle>{isTurkish ? 'Canli izleme' : 'Live monitor'}</CardTitle>
            <Badge variant={monitoringLive ? 'success' : sessionActive ? 'warning' : 'neutral'}>
              {monitoringLive ? (isTurkish ? 'AKTIF' : 'ACTIVE') : sessionActive ? (isTurkish ? 'OTURUM AKTIF' : 'SESSION ACTIVE') : isTurkish ? 'BOSTA' : 'IDLE'}
            </Badge>
            <Badge variant="primary">{permissionState.toUpperCase()}</Badge>
            {monitoringLive && showOverlay && mpState.loading && (
              <Badge variant="neutral" className="gap-1">
                <Loader2 className="size-3 animate-spin" />
                {isTurkish ? 'Model yükleniyor' : 'Loading model'}
              </Badge>
            )}
            {monitoringLive && showOverlay && mpState.ready && (
              <Badge variant="success">
                {isTurkish ? 'Canlı takip' : 'Live tracking'}
              </Badge>
            )}
            {isThrottled && (
              <Badge variant="warning">
                {isTurkish ? 'Analiz yavaşlatıldı' : 'Analysis throttled'}
              </Badge>
            )}
          </div>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Tarayici kamera onizlemesi, oturum kontrolleri ve kare analizi yuklenen masaustu panel tasarimi ile uyumlu.'
              : 'Browser camera preview, session controls, and frame analysis aligned with the uploaded desktop dashboard design.'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* ── Video + live canvas overlay ─────────────────────────────── */}
        <div className="relative overflow-hidden rounded-[28px] border border-[var(--line-soft)] bg-black">
          <video
            ref={videoRef}
            className={`aspect-video w-full object-cover transition-opacity ${streamReady ? 'opacity-100' : 'opacity-0'}`}
            autoPlay
            muted
            playsInline
          />

          {/* Live MediaPipe canvas — draws face mesh + hands at 30 fps */}
          <canvas
            ref={canvasRef}
            className="pointer-events-none absolute inset-0 h-full w-full"
            style={{ objectFit: 'cover' }}
          />

          {/* Server-analysis badges overlay (auth + behavior events) */}
          {showOverlay && (
            <div className="pointer-events-none absolute inset-0 z-10">
              {/* Face auth badge — top-right */}
              {auth && (
                <div className="absolute right-3 top-3">
                  <span
                    className={`rounded-md px-2 py-1 text-xs font-semibold text-white backdrop-blur-sm ${
                      !auth.enabled
                        ? 'bg-[rgba(100,100,100,0.82)]'
                        : auth.authenticated
                          ? 'bg-[rgba(34,197,94,0.82)]'
                          : 'bg-[rgba(239,68,68,0.82)]'
                    }`}
                  >
                    {!auth.enabled
                      ? isTurkish ? 'Yüz profili yok' : 'No face profile'
                      : auth.authenticated
                        ? `${isTurkish ? 'Doğrulandı' : 'Verified'} ${Math.round(auth.confidence * 100)}%`
                        : `${isTurkish ? 'Eşleşmedi' : 'No match'} ${Math.round(auth.confidence * 100)}%`}
                  </span>
                </div>
              )}

              {/* Behavior event strip — bottom */}
              {latestAnalysis?.vision_behavior_events && latestAnalysis.vision_behavior_events.length > 0 && (
                <div className="absolute inset-x-0 bottom-0 flex flex-wrap items-end gap-1.5 p-3">
                  {latestAnalysis.vision_behavior_events.map((evt, idx) => {
                    const bg =
                      evt.severity === 'high'
                        ? 'bg-[rgba(239,68,68,0.82)]'
                        : evt.severity === 'medium'
                          ? 'bg-[rgba(251,146,60,0.82)]'
                          : 'bg-[rgba(96,165,250,0.82)]'
                    return (
                      <span
                        key={idx}
                        className={`rounded-md px-2 py-0.5 text-xs font-semibold text-white backdrop-blur-sm ${bg}`}
                      >
                        {evt.event_type.replace(/_/g, ' ')}
                      </span>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {/* Scan line pulse when live */}
          {streamReady ? (
            <div className="pointer-events-none absolute inset-x-0 top-0 h-0.5 bg-[var(--primary)] shadow-[0_0_24px_var(--primary)] animate-[pulse_2.6s_ease-in-out_infinite]" />
          ) : null}

          {/* Offline placeholder */}
          {!streamReady ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-center">
              <div className="flex size-16 items-center justify-center rounded-3xl bg-[rgba(255,255,255,0.06)]">
                <VideoOff className="size-7 text-[var(--text-muted)]" />
              </div>
              <div className="space-y-2">
                <p className="text-base font-semibold text-white">{isTurkish ? 'Kamera onizlemesi cevrimdisi' : 'Camera preview is offline'}</p>
                <p className="max-w-md text-sm leading-6 text-[var(--text-muted)]">
                  {isTurkish
                    ? 'Canli analiz ve oturum destekli izleme icin tarayici kamera izni ver.'
                    : 'Grant browser camera permission to unlock live analysis and session-backed monitoring.'}
                </p>
              </div>
            </div>
          ) : null}
        </div>

        {cameraError ? <p className="text-sm text-[var(--danger)]">{cameraError}</p> : null}

        {sessionActive && !monitoringLive ? (
          <p className="text-sm text-[var(--warning)]">
            {isTurkish
              ? 'Arka uc oturumu aktif ama kamera akisi cevrimdisi. Kurtarmak icin kamerayi bagla veya oturumu durdur.'
              : 'Backend session is active but camera stream is offline. Reconnect camera or stop the session to recover.'}
          </p>
        ) : null}

        <div className="flex flex-col gap-3 md:flex-row md:flex-wrap">
          <Button variant="secondary" iconLeft={<Camera className="size-4" />} onClick={onRequestCamera}>
            {streamReady ? (isTurkish ? 'Kamerayi yenile' : 'Refresh camera') : isTurkish ? 'Kamera erisimi ver' : 'Grant camera access'}
          </Button>

          {sessionActive ? (
            <Button
              variant="danger"
              iconLeft={<Square className="size-4" />}
              loading={isStopping}
              onClick={onStopMonitoring}
            >
              {monitoringLive ? (isTurkish ? 'Izlemeyi durdur' : 'Stop monitoring') : isTurkish ? 'Oturumu durdur' : 'Stop session'}
            </Button>
          ) : (
            <Button
              variant="primary"
              iconLeft={<Play className="size-4" />}
              loading={isStarting}
              onClick={onStartMonitoring}
            >
              {isTurkish ? 'Izlemeyi baslat' : 'Start monitoring'}
            </Button>
          )}

          <Button
            variant="outline"
            iconLeft={<ScanFace className="size-4" />}
            loading={isAnalyzing}
            onClick={onAnalyzeNow}
            disabled={!canAnalyze}
          >
            {isTurkish ? 'Simdi analiz et' : 'Analyze now'}
          </Button>

          <Button
            variant="ghost"
            iconLeft={<UserRound className="size-4" />}
            onClick={onOpenFaceRegistration}
          >
            {isTurkish ? 'Yüz kaydı' : 'Face registration'}
          </Button>
        </div>

        {!analysisEnabled ? (
          <p className="text-sm text-[var(--warning)]">
            {isTurkish
              ? 'Kamera izleme ve uzak cikarim onayi birlikte etkin olana kadar analiz kapali.'
              : 'Analysis is disabled until camera monitoring and remote inference consent are both enabled.'}
          </p>
        ) : null}

        <div className="space-y-3">
          <div className="grid gap-3 rounded-[28px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4 md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <p className="text-sm font-semibold text-white">{isTurkish ? 'Surekli tarama' : 'Continuous scan'}</p>
              <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">
                {isTurkish
                  ? 'Oturum aktifken sürekli analiz eder. Görsel takip tarayıcıda anlık çalışır.'
                  : 'Continuously analyzes while the session is active. Visual tracking runs live in the browser.'}
              </p>
            </div>
            <Switch checked={autoScan} onCheckedChange={onToggleAutoScan} />
          </div>

          <div className="grid gap-3 rounded-[28px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4 md:grid-cols-[1fr_auto] md:items-center">
            <div>
              <p className="text-sm font-semibold text-white">{isTurkish ? 'Goruntu katmani' : 'Vision overlay'}</p>
              <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">
                {isTurkish
                  ? 'Yüz ağı ve el iskeletini canlı kamera üzerine çizer (tarayıcıda çalışır).'
                  : 'Draws face mesh and hand skeleton live on the camera feed (runs in the browser).'}
              </p>
            </div>
            <Switch checked={showOverlay} onCheckedChange={onToggleOverlay} />
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">{isTurkish ? 'Oturum Kimligi' : 'Session ID'}</p>
            <p className="mt-3 break-all text-sm font-semibold text-white">
              {activeSessionId ?? (isTurkish ? 'Aktif oturum yok' : 'No active session')}
            </p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">{isTurkish ? 'Varlik' : 'Presence'}</p>
            <p className="mt-3 text-sm font-semibold text-white">
              {latestAnalysis
                ? latestAnalysis.subject_present
                  ? isTurkish
                    ? 'Karede tespit edildi'
                    : 'Detected in frame'
                  : isTurkish
                    ? 'Tespit edilmedi'
                    : 'Not detected'
                : isTurkish
                  ? 'Analiz bekleniyor'
                  : 'Awaiting analysis'}
            </p>
          </div>
          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-xs uppercase tracking-[0.16em] text-[var(--text-soft)]">{isTurkish ? 'Kare durumu' : 'Frame status'}</p>
            <p className="mt-3 text-sm font-semibold text-white">
              {streamReady ? (isTurkish ? 'Canli onizleme hazir' : 'Live preview available') : isTurkish ? 'Kamera kullanilamiyor' : 'Camera unavailable'}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
