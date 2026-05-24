import { useEffect, useRef, useState } from 'react'
import { Camera, ScanFace } from 'lucide-react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import { authApi } from '@/api/auth'
import { toErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useCamera } from '@/hooks/use-camera'
import { useLanguage } from '@/i18n/language-provider'
import type { TokenResponse } from '@/types/auth'

type Props = {
  onSuccess: (session: TokenResponse) => void
  onSwitchToPassword: (email: string) => void
}

type FaceLoginPhase = 'form' | 'camera' | 'verifying' | 'error'

export function FaceLoginTab({ onSuccess, onSwitchToPassword }: Props) {
  const { isTurkish } = useLanguage()
  const { videoRef, permissionState, streamReady, errorMessage, requestCamera, stopCamera } = useCamera()

  const [phase, setPhase] = useState<FaceLoginPhase>('form')
  const [attemptCount, setAttemptCount] = useState(0)
  const [faceError, setFaceError] = useState<string | null>(null)
  const captureTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const schema = z.object({
    email: z.email(isTurkish ? 'Geçerli bir e-posta adresi gir.' : 'Enter a valid email address.'),
  })
  type FormValues = { email: string }
  const { register, handleSubmit, getValues, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  // Auto-capture after camera is ready
  useEffect(() => {
    if (phase === 'camera' && streamReady) {
      clearTimeout(captureTimerRef.current)
      captureTimerRef.current = setTimeout(() => void captureAndVerify(), 2000)
    }
    return () => clearTimeout(captureTimerRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, streamReady])

  // Stop camera when leaving camera phase
  useEffect(() => {
    if (phase !== 'camera' && phase !== 'verifying') {
      stopCamera()
    }
  }, [phase, stopCamera])

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

  async function captureAndVerify() {
    const email = getValues('email')
    const b64 = captureFrameBase64()
    if (!b64) {
      setFaceError(isTurkish ? 'Kamera görüntüsü alınamadı.' : 'Could not capture camera frame.')
      setPhase('error')
      return
    }

    setPhase('verifying')
    try {
      const session = await authApi.loginWithFace({
        email,
        face_image_base64: b64,
        image_content_type: 'image/jpeg',
      })
      stopCamera()
      toast.success(isTurkish ? 'Yüz ile giriş başarılı.' : 'Face login successful.')
      onSuccess(session)
    } catch (err: unknown) {
      const errObj = err as { response?: { data?: { code?: string } } }
      const code = errObj?.response?.data?.code
      if (code === 'FACE_NOT_REGISTERED') {
        toast.error(
          isTurkish
            ? 'Bu hesapta kayıtlı yüz yok. Şifre ile giriş yapın.'
            : 'No face registered for this account. Please use password login.',
        )
        stopCamera()
        onSwitchToPassword(email)
        return
      }

      const newCount = attemptCount + 1
      setAttemptCount(newCount)

      if (newCount >= 3) {
        toast.error(
          isTurkish
            ? 'Yüz tanıma 3 kez başarısız. Şifre ile giriş yapmayı deneyin.'
            : 'Face recognition failed 3 times. Please try password login.',
        )
        stopCamera()
        onSwitchToPassword(email)
        return
      }

      setFaceError(
        toErrorMessage(
          err,
          isTurkish
            ? 'Yüz tanıma başarısız. Tekrar deneyin.'
            : 'Face recognition failed. Please try again.',
        ),
      )
      setPhase('error')
    }
  }

  async function handleStartFaceLogin({ email: _ }: FormValues) {
    setFaceError(null)
    setAttemptCount(0)
    setPhase('camera')
    const granted = await requestCamera()
    if (!granted) {
      setPhase('form')
    }
  }

  function handleRetry() {
    setFaceError(null)
    setPhase('camera')
    captureTimerRef.current = setTimeout(() => void captureAndVerify(), 2000)
  }

  return (
    <div className="space-y-5">
      {/* Email field (always visible) */}
      <form onSubmit={handleSubmit(handleStartFaceLogin)} className="space-y-4">
        <Input
          label={isTurkish ? 'E-posta' : 'Email'}
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register('email')}
        />

        {/* Camera preview — shown only in camera / verifying phase */}
        {(phase === 'camera' || phase === 'verifying') && (
          <div className="relative overflow-hidden rounded-[20px] bg-black">
            <video
              ref={videoRef}
              className="aspect-video w-full object-cover"
              autoPlay
              muted
              playsInline
            />
            {/* Scanning badge */}
            {phase === 'verifying' && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black/50">
                <ScanFace className="size-10 animate-pulse text-[var(--primary)]" />
                <p className="text-sm font-medium text-white">
                  {isTurkish ? 'Doğrulanıyor...' : 'Verifying...'}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Error state */}
        {phase === 'error' && faceError && (
          <div className="rounded-[16px] border border-[var(--danger)]/30 bg-[rgba(239,68,68,0.08)] p-4">
            <p className="text-sm text-[var(--danger)]">{faceError}</p>
            <button
              type="button"
              className="mt-2 text-sm font-semibold text-white underline underline-offset-2"
              onClick={handleRetry}
            >
              {isTurkish ? 'Tekrar dene' : 'Try again'}
            </button>
          </div>
        )}

        {/* Hint during camera phase */}
        {phase === 'camera' && permissionState === 'granted' && !streamReady && (
          <p className="text-center text-sm text-[var(--text-muted)]">
            {isTurkish ? 'Kamera başlatılıyor...' : 'Starting camera...'}
          </p>
        )}
        {phase === 'camera' && streamReady && (
          <p className="text-center text-sm text-[var(--text-muted)]">
            <Camera className="mr-1 inline size-4" />
            {isTurkish ? 'Yüzünüzü kameraya gösterin...' : 'Position your face in front of the camera...'}
          </p>
        )}

        {/* Camera error */}
        {errorMessage && phase === 'form' && (
          <p className="text-sm text-[var(--danger)]">{errorMessage}</p>
        )}

        {/* Action button */}
        {phase === 'form' || phase === 'error' ? (
          <Button
            type="submit"
            className="w-full"
            size="lg"
            iconLeft={<ScanFace className="size-4" />}
          >
            {isTurkish ? 'Yüz ile Giriş Yap' : 'Sign in with Face'}
          </Button>
        ) : null}

        {phase === 'camera' && (
          <Button
            type="button"
            variant="secondary"
            className="w-full"
            onClick={() => { stopCamera(); setPhase('form') }}
          >
            {isTurkish ? 'İptal' : 'Cancel'}
          </Button>
        )}
      </form>
    </div>
  )
}
