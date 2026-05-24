import { useEffect, useRef, useState } from 'react'
import { Camera, CheckCircle, ChevronRight, SkipForward } from 'lucide-react'
import { toast } from 'sonner'
import { monitoringApi } from '@/api/monitoring'
import { toErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/button'
import { useCamera } from '@/hooks/use-camera'
import { useLanguage } from '@/i18n/language-provider'

type PoseStep = {
  key: 'front' | 'left' | 'right'
  label_tr: string
  label_en: string
  hint_tr: string
  hint_en: string
}

const POSE_STEPS: PoseStep[] = [
  {
    key: 'front',
    label_tr: 'Düz bakın',
    label_en: 'Look straight ahead',
    hint_tr: 'Kameraya doğrudan bakın',
    hint_en: 'Look directly at the camera',
  },
  {
    key: 'left',
    label_tr: 'Yavaşça sola dönün',
    label_en: 'Slowly turn left',
    hint_tr: 'Başınızı hafifçe sola çevirin',
    hint_en: 'Turn your head slightly to the left',
  },
  {
    key: 'right',
    label_tr: 'Yavaşça sağa dönün',
    label_en: 'Slowly turn right',
    hint_tr: 'Başınızı hafifçe sağa çevirin',
    hint_en: 'Turn your head slightly to the right',
  },
]

const CAPTURE_DELAY_MS = 2000

type Props = {
  onComplete: (skipped: boolean) => void
}

export function FaceRegistrationStep({ onComplete }: Props) {
  const { isTurkish } = useLanguage()
  const { videoRef, permissionState, errorMessage, streamReady, requestCamera } = useCamera()
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const captureTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const [poseIndex, setPoseIndex] = useState(0)
  const [framesEnrolled, setFramesEnrolled] = useState(0)
  const [status, setStatus] = useState<'idle' | 'capturing' | 'success' | 'error'>('idle')
  const [captureError, setCaptureError] = useState<string | null>(null)
  const [lastCaptureFeedback, setLastCaptureFeedback] = useState<boolean | null>(null)
  const isCapturingRef = useRef(false)

  const cameraGranted = permissionState === 'granted' && streamReady

  // Draw oval guide overlay on canvas whenever video is ready
  useEffect(() => {
    if (!streamReady) return

    const canvas = canvasRef.current
    const video = videoRef.current
    if (!canvas || !video) return

    let rafId: number
    function drawOverlay() {
      const ctx = canvas!.getContext('2d')
      if (!ctx || !video) return
      canvas!.width = video.videoWidth || 640
      canvas!.height = video.videoHeight || 480
      ctx.clearRect(0, 0, canvas!.width, canvas!.height)

      // Draw oval
      const cx = canvas!.width / 2
      const cy = canvas!.height / 2
      const rx = canvas!.width * 0.28
      const ry = canvas!.height * 0.42

      ctx.beginPath()
      ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2)
      ctx.strokeStyle = lastCaptureFeedback === true
        ? 'rgba(34,197,94,0.9)'
        : lastCaptureFeedback === false
          ? 'rgba(239,68,68,0.9)'
          : 'rgba(255,255,255,0.6)'
      ctx.lineWidth = 3
      ctx.stroke()

      rafId = requestAnimationFrame(drawOverlay)
    }

    drawOverlay()
    return () => cancelAnimationFrame(rafId)
  }, [streamReady, lastCaptureFeedback, videoRef])

  function captureFrameBase64(): string | null {
    const video = videoRef.current
    if (!video || video.videoWidth === 0) return null
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    ctx.drawImage(video, 0, 0)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.88)
    return dataUrl.split(',')[1] ?? null
  }

  async function captureAndSend(poseKey: PoseStep['key']) {
    if (isCapturingRef.current) return
    isCapturingRef.current = true
    setStatus('capturing')

    const b64 = captureFrameBase64()
    if (!b64) {
      isCapturingRef.current = false
      return
    }

    try {
      const result = await monitoringApi.registerFace({
        image_base64: b64,
        image_content_type: 'image/jpeg',
        pose_hint: poseKey,
      })
      setLastCaptureFeedback(result.success)
      setFramesEnrolled(result.frames_enrolled)

      if (result.success) {
        const next = poseIndex + 1
        if (next >= POSE_STEPS.length) {
          // All required poses done
          setStatus('success')
          toast.success(isTurkish ? 'Yüz kaydı tamamlandı!' : 'Face registration complete!')
          setTimeout(() => onComplete(false), 2000)
        } else {
          setLastCaptureFeedback(null)
          setPoseIndex(next)
          setStatus('idle')
        }
      } else {
        // Frame didn't detect a face — schedule retry
        setStatus('idle')
        captureTimerRef.current = setTimeout(() => captureAndSend(poseKey), CAPTURE_DELAY_MS)
      }
    } catch (err) {
      setCaptureError(toErrorMessage(err, isTurkish ? 'Yüz kaydedilemedi.' : 'Face capture failed.'))
      setStatus('error')
    } finally {
      isCapturingRef.current = false
    }
  }

  function startCapture() {
    const pose = POSE_STEPS[poseIndex]
    if (!pose) return
    clearTimeout(captureTimerRef.current)
    captureTimerRef.current = setTimeout(() => captureAndSend(pose.key), CAPTURE_DELAY_MS)
  }

  // Cleanup timer on unmount
  useEffect(() => () => clearTimeout(captureTimerRef.current), [])

  const currentPose = POSE_STEPS[poseIndex]

  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-lg font-semibold text-white">
          {isTurkish ? 'Yüz Kaydı' : 'Face Registration'}
        </h3>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          {isTurkish
            ? 'Yüz tanıma için 3 açıdan fotoğrafınız alınacak.'
            : 'We will capture your face from 3 angles for recognition.'}
        </p>
      </div>

      {/* Progress indicator */}
      <div className="flex gap-2">
        {POSE_STEPS.map((pose, i) => (
          <div
            key={pose.key}
            className={`h-1.5 flex-1 rounded-full transition-all ${
              i < poseIndex
                ? 'bg-[var(--success)]'
                : i === poseIndex
                  ? 'bg-[var(--primary)]'
                  : 'bg-[var(--surface-muted)]'
            }`}
          />
        ))}
      </div>

      {/* Camera area */}
      {!cameraGranted ? (
        <div className="flex flex-col items-center gap-4 rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface-subtle)] p-8 text-center">
          <div className="flex size-14 items-center justify-center rounded-3xl bg-[var(--surface-muted)]">
            <Camera className="size-6 text-[var(--text-muted)]" />
          </div>
          <p className="text-sm text-[var(--text-muted)]">
            {isTurkish
              ? 'Yüz kaydı için kamera erişimi gereklidir.'
              : 'Camera access is required for face registration.'}
          </p>
          {errorMessage && <p className="text-sm text-[var(--danger)]">{errorMessage}</p>}
          <Button
            variant="primary"
            iconLeft={<Camera className="size-4" />}
            onClick={() => void requestCamera()}
          >
            {isTurkish ? 'Kamera İznini Ver' : 'Grant Camera Access'}
          </Button>
        </div>
      ) : (
        <div className="relative overflow-hidden rounded-[24px] bg-black">
          {/* Video */}
          <video
            ref={videoRef}
            className="aspect-video w-full object-cover"
            autoPlay
            muted
            playsInline
          />
          {/* Overlay canvas */}
          <canvas
            ref={canvasRef}
            className="pointer-events-none absolute inset-0 h-full w-full"
          />

          {/* Done overlay */}
          {status === 'success' && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/60">
              <CheckCircle className="size-12 text-[var(--success)]" />
              <p className="text-base font-semibold text-white">
                {isTurkish ? 'Yüz kaydı tamamlandı!' : 'Face registration complete!'}
              </p>
              <p className="text-sm text-[var(--text-muted)]">
                {isTurkish ? `${framesEnrolled} kare kaydedildi` : `${framesEnrolled} frames enrolled`}
              </p>
            </div>
          )}

          {/* Per-frame feedback badge */}
          {lastCaptureFeedback !== null && status !== 'success' && (
            <div className="absolute right-3 top-3">
              <span
                className={`rounded-md px-2 py-1 text-xs font-semibold text-white backdrop-blur-sm ${
                  lastCaptureFeedback
                    ? 'bg-[rgba(34,197,94,0.82)]'
                    : 'bg-[rgba(239,68,68,0.82)]'
                }`}
              >
                {lastCaptureFeedback
                  ? isTurkish ? 'Yüz algılandı ✓' : 'Face detected ✓'
                  : isTurkish ? 'Yüz bulunamadı' : 'No face found'}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      {cameraGranted && status !== 'success' && currentPose && (
        <div className="rounded-[20px] border border-[var(--line-soft)] bg-[var(--surface-subtle)] p-4 text-center">
          <p className="text-base font-semibold text-white">
            {isTurkish ? currentPose.label_tr : currentPose.label_en}
          </p>
          <p className="mt-1 text-sm text-[var(--text-muted)]">
            {isTurkish ? currentPose.hint_tr : currentPose.hint_en}
          </p>
          {captureError && (
            <p className="mt-2 text-sm text-[var(--danger)]">{captureError}</p>
          )}
        </div>
      )}

      {/* Actions */}
      {cameraGranted && status !== 'success' && (
        <div className="flex flex-col gap-3">
          <Button
            variant="primary"
            className="w-full"
            loading={status === 'capturing'}
            disabled={status === 'capturing'}
            onClick={startCapture}
            iconLeft={<ChevronRight className="size-4" />}
          >
            {status === 'capturing'
              ? isTurkish ? 'Kaydediliyor...' : 'Capturing...'
              : poseIndex === 0
                ? isTurkish ? 'Yüz Kaydını Başlat' : 'Start Face Registration'
                : isTurkish ? 'Sonraki Pose' : 'Next Pose'}
          </Button>
          <button
            type="button"
            className="flex items-center justify-center gap-2 text-sm text-[var(--text-muted)] transition hover:text-[var(--text-strong)]"
            onClick={() => onComplete(true)}
          >
            <SkipForward className="size-4" />
            {isTurkish
              ? 'Şimdilik atla (sınırlı özellikler)'
              : 'Skip for now (limited features)'}
          </button>
        </div>
      )}

      {!cameraGranted && (
        <button
          type="button"
          className="w-full text-center text-sm text-[var(--text-muted)] transition hover:text-[var(--text-strong)]"
          onClick={() => onComplete(true)}
        >
          <SkipForward className="inline mr-1 size-4" />
          {isTurkish ? 'Yüz kaydı olmadan devam et' : 'Continue without face registration'}
        </button>
      )}
    </div>
  )
}
