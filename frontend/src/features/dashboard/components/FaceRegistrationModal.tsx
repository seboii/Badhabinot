import { useEffect, useRef, useState } from 'react'
import { CheckCircle, Trash2, UserRound, X } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { monitoringApi } from '@/api/monitoring'
import { toErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { useLanguage } from '@/i18n/language-provider'

const TOTAL_FRAMES = 8
const CAPTURE_INTERVAL_MS = 1500
const COUNTDOWN_SECONDS = 3

type Phase = 'idle' | 'countdown' | 'capturing' | 'done' | 'error'

type FaceRegistrationModalProps = {
  onClose: () => void
}

export function FaceRegistrationModal({ onClose }: FaceRegistrationModalProps) {
  const { isTurkish } = useLanguage()

  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const captureTimerRef = useRef<number | undefined>(undefined)

  const [phase, setPhase] = useState<Phase>('idle')
  const [countdown, setCountdown] = useState(COUNTDOWN_SECONDS)
  const [capturedCount, setCapturedCount] = useState(0)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [framesEnrolled, setFramesEnrolled] = useState(0)
  const [lastFrameDetected, setLastFrameDetected] = useState<boolean | null>(null)
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)

  const deleteProfileMutation = useMutation({
    mutationFn: monitoringApi.deleteFaceProfile,
    onSuccess() {
      toast.success(isTurkish ? 'Yüz profili silindi.' : 'Face profile deleted.')
      onClose()
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Yüz profili silinemedi.' : 'Unable to delete face profile.'))
      setDeleteConfirmOpen(false)
    },
  })

  // Start camera on mount
  useEffect(() => {
    let mounted = true

    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false,
        })
        if (!mounted) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = stream
        const video = videoRef.current
        if (video) {
          video.srcObject = stream
          video.autoplay = true
          video.muted = true
          video.playsInline = true
          await video.play()
        }
      } catch {
        if (mounted) {
          setCameraError(
            isTurkish
              ? 'Kameraya erisim saglanamadi. Lutfen kamera iznini kontrol edin.'
              : 'Unable to access camera. Please check camera permission.',
          )
        }
      }
    }

    void startCamera()

    return () => {
      mounted = false
      window.clearInterval(captureTimerRef.current)
      streamRef.current?.getTracks().forEach((t) => t.stop())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function captureFrameBase64(): string | null {
    const video = videoRef.current
    if (!video || video.videoWidth === 0 || video.videoHeight === 0) {
      return null
    }
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.88)
    return dataUrl.split(',')[1] ?? null
  }

  function startCountdown() {
    setPhase('countdown')
    setCountdown(COUNTDOWN_SECONDS)
    setCapturedCount(0)
    setFramesEnrolled(0)
    setCameraError(null)
    setLastFrameDetected(null)

    let remaining = COUNTDOWN_SECONDS
    const tick = window.setInterval(() => {
      remaining -= 1
      setCountdown(remaining)
      if (remaining <= 0) {
        window.clearInterval(tick)
        startCapturing()
      }
    }, 1000)
  }

  function startCapturing() {
    setPhase('capturing')
    let captured = 0

    const doCapture = async () => {
      const b64 = captureFrameBase64()
      if (!b64) {
        captured += 1
        setCapturedCount(captured)
        if (captured >= TOTAL_FRAMES) {
          finishCapture(0)
          return
        }
        return
      }

      try {
        const result = await monitoringApi.registerFace({
          image_base64: b64,
          image_content_type: 'image/jpeg',
        })
        setLastFrameDetected(result.success)
        captured += 1
        setCapturedCount(captured)
        setFramesEnrolled(result.frames_enrolled)
        if (captured >= TOTAL_FRAMES) {
          window.clearInterval(captureTimerRef.current)
          finishCapture(result.frames_enrolled)
        }
      } catch (error) {
        window.clearInterval(captureTimerRef.current)
        setPhase('error')
        setCameraError(toErrorMessage(error, isTurkish ? 'Yuz kaydedilemedi.' : 'Face registration failed.'))
      }
    }

    // Fire first capture immediately, then on interval
    void doCapture()
    captureTimerRef.current = window.setInterval(() => {
      void doCapture()
    }, CAPTURE_INTERVAL_MS)
  }

  function finishCapture(enrolled: number) {
    setPhase('done')
    toast.success(
      isTurkish
        ? `Yuz kaydı tamamlandi. ${enrolled} kare kaydedildi.`
        : `Face registration complete. ${enrolled} frames enrolled.`,
    )
  }

  const isRunning = phase === 'countdown' || phase === 'capturing'

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isRunning) onClose()
      }}
    >
      <div className="relative mx-4 w-full max-w-md rounded-[32px] border border-[var(--line-soft)] bg-[var(--surface-soft)] p-6 shadow-2xl">
        {/* Close button */}
        {!isRunning ? (
          <button
            className="absolute right-5 top-5 flex size-8 items-center justify-center rounded-full bg-[var(--surface-hover)] text-[var(--text-muted)] transition hover:text-white"
            onClick={onClose}
            aria-label={isTurkish ? 'Kapat' : 'Close'}
          >
            <X className="size-4" />
          </button>
        ) : null}

        <div className="mb-5 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-2xl bg-[var(--primary-soft)]">
            <UserRound className="size-5 text-[var(--primary)]" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">
              {isTurkish ? 'Yüz kaydı' : 'Face registration'}
            </h2>
            <p className="text-sm text-[var(--text-muted)]">
              {isTurkish ? '8 kare ile yüzünüzü kaydedin' : 'Enrol your face with 8 frames'}
            </p>
          </div>
        </div>

        {/* Camera preview */}
        <div
          className={`relative overflow-hidden rounded-[20px] bg-black transition-shadow duration-300 ${
            phase === 'capturing' && lastFrameDetected === true
              ? 'ring-2 ring-[var(--success)]'
              : phase === 'capturing' && lastFrameDetected === false
                ? 'ring-2 ring-[var(--danger)]'
                : ''
          }`}
        >
          <video
            ref={videoRef}
            className="aspect-video w-full object-cover"
            autoPlay
            muted
            playsInline
          />

          {/* Per-frame face detection badge */}
          {phase === 'capturing' && lastFrameDetected !== null ? (
            <div className="absolute right-3 top-3">
              <span
                className={`rounded-md px-2 py-1 text-xs font-semibold text-white backdrop-blur-sm ${
                  lastFrameDetected ? 'bg-[rgba(34,197,94,0.82)]' : 'bg-[rgba(239,68,68,0.82)]'
                }`}
              >
                {lastFrameDetected
                  ? isTurkish ? 'Yüz algılandı ✓' : 'Face detected ✓'
                  : isTurkish ? 'Yüz bulunamadı' : 'No face found'}
              </span>
            </div>
          ) : null}

          {/* Countdown overlay */}
          {phase === 'countdown' ? (
            <div className="absolute inset-0 flex items-center justify-center bg-black/50">
              <span className="text-7xl font-black text-white drop-shadow-lg">{countdown}</span>
            </div>
          ) : null}

          {/* Progress ring/flash during capture */}
          {phase === 'capturing' ? (
            <div className="absolute inset-x-0 top-0 h-1 bg-[var(--surface-muted)]">
              <div
                className="h-1 bg-[var(--primary)] transition-all duration-300"
                style={{ width: `${(capturedCount / TOTAL_FRAMES) * 100}%` }}
              />
            </div>
          ) : null}

          {/* Done overlay */}
          {phase === 'done' ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/60">
              <CheckCircle className="size-12 text-[var(--success)]" />
              <p className="text-base font-semibold text-white">
                {isTurkish ? 'Kayıt tamamlandı' : 'Registration complete'}
              </p>
              {framesEnrolled > 0 ? (
                <p className="text-sm text-[var(--text-muted)]">
                  {isTurkish ? `${framesEnrolled} kare kaydedildi` : `${framesEnrolled} frames enrolled`}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>

        {cameraError ? (
          <p className="mt-3 text-sm text-[var(--danger)]">{cameraError}</p>
        ) : null}

        {/* Progress text */}
        {phase === 'capturing' ? (
          <p className="mt-3 text-center text-sm text-[var(--text-muted)]">
            {isTurkish
              ? `Kare ${capturedCount} / ${TOTAL_FRAMES} yakalanıyor...`
              : `Capturing frame ${capturedCount} / ${TOTAL_FRAMES}...`}
          </p>
        ) : null}

        {/* Actions */}
        <div className="mt-5 flex gap-3">
          {phase === 'idle' || phase === 'error' ? (
            <>
              <Button variant="secondary" className="flex-1" onClick={onClose}>
                {isTurkish ? 'İptal' : 'Cancel'}
              </Button>
              <Button variant="primary" className="flex-1" onClick={startCountdown} disabled={Boolean(cameraError)}>
                {phase === 'error'
                  ? isTurkish ? 'Tekrar dene' : 'Try again'
                  : isTurkish ? 'Taramayı başlat' : 'Start scan'}
              </Button>
            </>
          ) : phase === 'done' ? (
            <Button variant="primary" className="w-full" onClick={onClose}>
              {isTurkish ? 'Tamam' : 'Done'}
            </Button>
          ) : (
            <p className="w-full text-center text-sm text-[var(--text-muted)]">
              {phase === 'countdown'
                ? isTurkish ? 'Hazırlanıyor...' : 'Get ready...'
                : isTurkish ? 'Yüzünüzü kameraya bakın' : 'Keep your face in view of the camera'}
            </p>
          )}
        </div>

        {phase === 'idle' || phase === 'done' ? (
          <div className="mt-4 flex justify-center">
            <button
              type="button"
              onClick={() => setDeleteConfirmOpen(true)}
              className="flex items-center gap-1.5 text-xs text-[var(--text-soft)] transition hover:text-[var(--danger)]"
            >
              <Trash2 className="size-3" />
              {isTurkish ? 'Kayıtlı yüzü sil' : 'Delete face profile'}
            </button>
          </div>
        ) : null}
      </div>

      <ConfirmDialog
        isOpen={deleteConfirmOpen}
        variant="danger"
        title={isTurkish ? 'Yüz profilini sil' : 'Delete face profile'}
        description={
          isTurkish
            ? 'Bu işlem kayıtlı yüz verinizi kalıcı olarak siler. Yüz tanıma devre dışı kalır.'
            : 'This permanently deletes your enrolled face data. Face recognition will be disabled.'
        }
        confirmLabel={isTurkish ? 'Sil' : 'Delete'}
        cancelLabel={isTurkish ? 'Vazgeç' : 'Cancel'}
        loading={deleteProfileMutation.isPending}
        onConfirm={() => deleteProfileMutation.mutate()}
        onCancel={() => setDeleteConfirmOpen(false)}
      />
    </div>
  )
}
