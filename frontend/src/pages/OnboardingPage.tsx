import { useMemo, useState } from 'react'
import { Camera, ChevronLeft, ChevronRight, Lock, ShieldCheck } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { userApi } from '@/api/user'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingScreen } from '@/components/ui/loading-state'
import { ProgressStepper } from '@/components/ui/progress-stepper'
import { Switch } from '@/components/ui/switch'
import { useCamera } from '@/hooks/use-camera'
import { LanguageToggle } from '@/i18n/language-toggle'
import { useLanguage } from '@/i18n/language-provider'
import { ThemeToggle } from '@/theme/theme-toggle'

type OnboardingValues = {
  privacy_policy_accepted: boolean
  camera_monitoring_accepted: boolean
  remote_inference_accepted: boolean
}

export function OnboardingPage() {
  const { isTurkish } = useLanguage()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['user-context'],
    queryFn: userApi.getMe,
  })
  const { videoRef, permissionState, streamReady, errorMessage, requestCamera } = useCamera()

  const [step, setStep] = useState(1)
  const [values, setValues] = useState<OnboardingValues>({
    privacy_policy_accepted: false,
    camera_monitoring_accepted: false,
    remote_inference_accepted: false,
  })

  const completeMutation = useMutation({
    mutationFn: async (payload: OnboardingValues) => {
      await userApi.updateConsents(payload)
    },
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['user-context'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      toast.success(
        isTurkish
          ? 'Baslangic tamamlandi. Artik panelden izlemeyi baslatabilirsin.'
          : 'Onboarding completed. You can now start monitoring from the dashboard.',
      )
      navigate('/dashboard', { replace: true })
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Baslangic tamamlanamadi.' : 'Unable to complete onboarding.'))
    },
  })

  const readyToStart = useMemo(() => permissionState === 'granted' && streamReady, [permissionState, streamReady])

  // 2 steps: 1 = all consents, 2 = camera access
  const steps = [
    { title: isTurkish ? 'Gizlilik ve Onaylar' : 'Privacy & Consents' },
    { title: isTurkish ? 'Kamera İzni' : 'Camera Access' },
  ]

  const allConsentsGiven =
    values.privacy_policy_accepted &&
    values.camera_monitoring_accepted &&
    values.remote_inference_accepted

  function handleToggle(key: keyof OnboardingValues, checked: boolean) {
    setValues((prev) => ({ ...prev, [key]: checked }))
  }

  function handleComplete() {
    if (!readyToStart) {
      toast.error(
        isTurkish ? 'Izlemeyi baslatmadan once kamera erisimi ver.' : 'Grant camera access before starting monitoring.',
      )
      return
    }
    completeMutation.mutate(values)
  }

  if (isLoading || !data) {
    return <LoadingScreen message={isTurkish ? 'Guvenli baslangic hazirlaniyor' : 'Preparing secure onboarding'} />
  }

  return (
    <div className="min-h-screen px-5 py-8 md:px-8">
      <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        {/* Left hero */}
        <section className="rounded-[36px] border border-[var(--line-soft)] bg-[var(--hero-surface)] p-8 shadow-[var(--shadow-panel)] md:p-10">
          <div className="flex items-start justify-between gap-4">
            <Badge variant="primary" className="mb-5 gap-2 px-3 py-1.5">
              <ShieldCheck className="size-4" />
              {isTurkish ? 'Hos geldin,' : 'Welcome,'} {data.display_name}
            </Badge>
            <div className="flex items-center gap-2">
              <LanguageToggle />
              <ThemeToggle />
            </div>
          </div>
          <h1 className="max-w-2xl text-4xl font-extrabold tracking-[-0.05em] text-[var(--text-strong)] md:text-5xl">
            {isTurkish ? 'API destekli canli izlemeyi etkinlestir' : 'Activate API-backed live monitoring'}
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--text-muted)]">
            {isTurkish
              ? 'Duzenlenen BADHABINOT akisinda acik kamera izni ve onay hala gerekir, fakat ust seviye analiz artik yerel model yerine harici AI bagdastirici servisinden geciyor.'
              : 'The repaired BADHABINOT flow still asks for explicit camera permission and consent, but higher-level analysis is now routed through the external AI adapter service instead of a local model runtime.'}
          </p>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <Card className="bg-[rgba(255,255,255,0.03)]">
              <CardContent className="p-5">
                <p className="text-sm font-semibold text-white">{isTurkish ? 'Mevcut mod' : 'Current mode'}</p>
                <p className="mt-3 text-2xl font-bold text-white">{data.settings.model_mode}</p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">
                  {isTurkish
                    ? 'Arka uc orkestrasyonunda kullanilan kayitli analiz modu.'
                    : 'Persisted analysis mode used by the backend orchestration.'}
                </p>
              </CardContent>
            </Card>
            <Card className="bg-[rgba(255,255,255,0.03)]">
              <CardContent className="p-5">
                <p className="text-sm font-semibold text-white">{isTurkish ? 'Su araligi' : 'Water interval'}</p>
                <p className="mt-3 text-2xl font-bold text-white">{data.settings.water_interval_min} min</p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">
                  {isTurkish ? 'Su hatirlatici araligi zaten ayarli.' : 'Reminder cadence already configured for hydration.'}
                </p>
              </CardContent>
            </Card>
            <Card className="bg-[rgba(255,255,255,0.03)]">
              <CardContent className="p-5">
                <p className="text-sm font-semibold text-white">{isTurkish ? 'Sessiz saatler' : 'Quiet hours'}</p>
                <p className="mt-3 text-2xl font-bold text-white">
                  {data.settings.quiet_hours_enabled ? (isTurkish ? 'Acik' : 'Enabled') : isTurkish ? 'Kapali' : 'Off'}
                </p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">
                  {isTurkish
                    ? 'Tercih ettigin saatler disinda hatirlatici gonderimini sustur.'
                    : 'Silence reminder delivery outside your preferred hours.'}
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Right step panel */}
        <section className="space-y-6">
          <Card>
            <CardContent className="p-6">
              <ProgressStepper steps={steps} currentStep={step} />
            </CardContent>
          </Card>

          {/* ── Step 1: all consents in one screen ── */}
          {step === 1 && (
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>{isTurkish ? 'Gizlilik ve Onaylar' : 'Privacy & Consents'}</CardTitle>
                  <CardDescription className="mt-2">
                    {isTurkish
                      ? 'Platformu kullanmak için aşağıdaki izinleri onaylamanız gerekmektedir.'
                      : 'You must accept the following permissions to use the platform.'}
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Privacy policy */}
                <div className="flex items-center justify-between gap-4 rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                  <div>
                    <p className="text-sm font-semibold text-white">
                      {isTurkish ? 'Gizlilik politikası kabul edildi' : 'Privacy policy accepted'}
                    </p>
                    <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">
                      {isTurkish
                        ? 'İzleme, panel ve geçmiş akışlarını kullanmaya devam etmek için zorunlu.'
                        : 'Required to keep using monitoring, dashboard, and history workflows.'}
                    </p>
                  </div>
                  <Switch
                    checked={values.privacy_policy_accepted}
                    onCheckedChange={(checked) => handleToggle('privacy_policy_accepted', checked)}
                  />
                </div>

                {/* Camera monitoring */}
                <div className="flex items-center justify-between gap-4 rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                  <div>
                    <p className="text-sm font-semibold text-white">
                      {isTurkish ? 'Kamera izleme onayı' : 'Camera monitoring consent'}
                    </p>
                    <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">
                      {isTurkish
                        ? 'Canlı kamera hattının kareleri anlık çıkarım için işlemesine izin verir.'
                        : 'Allows the live camera pipeline to process frames for immediate inference.'}
                    </p>
                  </div>
                  <Switch
                    checked={values.camera_monitoring_accepted}
                    onCheckedChange={(checked) => handleToggle('camera_monitoring_accepted', checked)}
                  />
                </div>

                {/* Remote inference */}
                <div className="flex items-center justify-between gap-4 rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-white">
                        {isTurkish ? 'Uzak çıkarım onayı' : 'Remote inference consent'}
                      </p>
                      <Lock className="size-4 text-[var(--text-muted)]" />
                    </div>
                    <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">
                      {isTurkish
                        ? 'Zorunlu. Üst seviye analiz harici AI bağdaştırıcı servisinde yapılır.'
                        : 'Required. Higher-level analysis is performed through the external AI adapter service.'}
                    </p>
                  </div>
                  <Switch
                    checked={values.remote_inference_accepted}
                    onCheckedChange={(checked) => handleToggle('remote_inference_accepted', checked)}
                  />
                </div>

                {/* Info note */}
                <div className="rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4 text-sm leading-6 text-[var(--text-muted)]">
                  {isTurkish
                    ? 'Görüntü ön işleme vision-service içinde yerelde kalır, ancak davranış yorumlama harici API tabanlıdır.'
                    : 'Vision preprocessing stays local in the vision-service, but behavior interpretation is external-API driven.'}
                </div>

                {/* KVKK link */}
                <p className="text-xs text-[var(--text-muted)]">
                  {isTurkish ? (
                    <>
                      Devam ederek{' '}
                      <Link to="/kvkk" target="_blank" className="font-semibold text-white underline underline-offset-2">
                        KVKK Aydınlatma Metnini
                      </Link>{' '}
                      ve{' '}
                      <Link to="/privacy" target="_blank" className="font-semibold text-white underline underline-offset-2">
                        Gizlilik Politikasını
                      </Link>{' '}
                      okuduğunuzu ve kabul ettiğinizi beyan edersiniz.
                    </>
                  ) : (
                    <>
                      By continuing you confirm that you have read and accepted the{' '}
                      <Link to="/kvkk" target="_blank" className="font-semibold text-white underline underline-offset-2">
                        KVKK Disclosure
                      </Link>{' '}
                      and{' '}
                      <Link to="/privacy" target="_blank" className="font-semibold text-white underline underline-offset-2">
                        Privacy Policy
                      </Link>.
                    </>
                  )}
                </p>

                <div className="flex justify-end">
                  <Button
                    variant="primary"
                    iconLeft={<ChevronRight className="size-4" />}
                    disabled={!allConsentsGiven}
                    onClick={() => setStep(2)}
                  >
                    {isTurkish ? 'İleri' : 'Next'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ── Step 2: camera access ── */}
          {step === 2 && (
            <Card>
              <CardHeader>
                <div>
                  <CardTitle>{isTurkish ? 'Kamera İzni' : 'Camera Access'}</CardTitle>
                  <CardDescription className="mt-2">
                    {isTurkish
                      ? 'BADHABINOT canlı oturum başlatmadan önce kamera erişimi gerekir.'
                      : 'Camera access is required before BADHABINOT can start a live session.'}
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="overflow-hidden rounded-[28px] border border-[var(--line-soft)] bg-black">
                  <div className="relative">
                    <video
                      ref={videoRef}
                      className={`aspect-video w-full object-cover transition-opacity ${streamReady ? 'opacity-100' : 'opacity-0'}`}
                      autoPlay
                      muted
                      playsInline
                    />
                    {!streamReady ? (
                      <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 text-center">
                        <div className="flex size-14 items-center justify-center rounded-3xl bg-[var(--surface-muted)]">
                          <Camera className="size-6 text-[var(--text-muted)]" />
                        </div>
                        <p className="max-w-sm text-sm leading-6 text-[var(--text-muted)]">
                          {isTurkish
                            ? 'Henüz önizleme yok. Kamera erişimi vermek için aşağıdaki düğmeye tıklayın.'
                            : 'No preview yet. Click the button below to grant camera access.'}
                        </p>
                      </div>
                    ) : null}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <Button variant="secondary" iconLeft={<Camera className="size-4" />} onClick={() => void requestCamera()}>
                    {streamReady
                      ? isTurkish ? 'Kamera iznini yenile' : 'Refresh camera permission'
                      : isTurkish ? 'Kamera erişimi ver' : 'Grant camera access'}
                  </Button>
                  <Badge variant={readyToStart ? 'success' : 'warning'}>
                    {readyToStart ? (isTurkish ? 'Kamera hazır' : 'Camera ready') : permissionState.toUpperCase()}
                  </Badge>
                </div>

                {errorMessage ? <p className="text-sm text-[var(--danger)]">{errorMessage}</p> : null}

                <div className="flex justify-between">
                  <Button variant="secondary" iconLeft={<ChevronLeft className="size-4" />} onClick={() => setStep(1)}>
                    {isTurkish ? 'Geri' : 'Back'}
                  </Button>
                  <Button
                    variant="primary"
                    size="lg"
                    iconLeft={<ChevronRight className="size-4" />}
                    loading={completeMutation.isPending}
                    disabled={!readyToStart}
                    onClick={handleComplete}
                  >
                    {isTurkish ? 'Kabul et ve izlemeyi başlat' : 'Accept and start monitoring'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </section>
      </div>
    </div>
  )
}
