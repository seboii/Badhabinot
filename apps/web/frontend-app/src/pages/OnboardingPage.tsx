import { useMemo } from 'react'
import { Camera, ChevronRight, Lock, ShieldCheck } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { toErrorMessage } from '@/api/client'
import { userApi } from '@/api/user'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingScreen } from '@/components/ui/loading-state'
import { Switch } from '@/components/ui/switch'
import { useCamera } from '@/hooks/use-camera'
import { ThemeToggle } from '@/theme/theme-toggle'

const onboardingSchema = z.object({
  privacy_policy_accepted: z.boolean().refine((value) => value, {
    message: 'You must accept the privacy policy to continue.',
  }),
  camera_monitoring_accepted: z.boolean().refine((value) => value, {
    message: 'Camera monitoring consent is required to start live analysis.',
  }),
  remote_inference_accepted: z.boolean().refine((value) => value, {
    message: 'Remote inference consent is required because higher-level analysis is API-based.',
  }),
})

type OnboardingValues = z.infer<typeof onboardingSchema>

export function OnboardingPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['user-context'],
    queryFn: userApi.getMe,
  })
  const { videoRef, permissionState, streamReady, errorMessage, requestCamera } = useCamera()

  const {
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<OnboardingValues>({
    resolver: zodResolver(onboardingSchema),
    values: {
      privacy_policy_accepted: data?.consents.privacy_policy_accepted ?? false,
      camera_monitoring_accepted: data?.consents.camera_monitoring_accepted ?? false,
      remote_inference_accepted: data?.consents.remote_inference_accepted ?? false,
    },
  })

  const completeMutation = useMutation({
    mutationFn: async (values: OnboardingValues) => {
      await userApi.updateConsents(values)
    },
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['user-context'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      void queryClient.invalidateQueries({ queryKey: ['activities'] })
      toast.success('Onboarding completed. You can now start monitoring from the dashboard.')
      navigate('/dashboard', { replace: true })
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to complete onboarding.'))
    },
  })

  const readyToStart = useMemo(() => permissionState === 'granted' && streamReady, [permissionState, streamReady])

  if (isLoading || !data) {
    return <LoadingScreen message="Preparing secure onboarding" />
  }

  return (
    <div className="min-h-screen px-5 py-8 md:px-8">
      <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-[36px] border border-[var(--line-soft)] bg-[var(--hero-surface)] p-8 shadow-[var(--shadow-panel)] md:p-10">
          <div className="flex items-start justify-between gap-4">
            <Badge variant="primary" className="mb-5 gap-2 px-3 py-1.5">
              <ShieldCheck className="size-4" />
              Welcome, {data.display_name}
            </Badge>
            <ThemeToggle />
          </div>
          <h1 className="max-w-2xl text-4xl font-extrabold tracking-[-0.05em] text-[var(--text-strong)] md:text-5xl">
            Activate API-backed live monitoring
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--text-muted)]">
            The repaired BADHABINOT flow still asks for explicit camera permission and consent, but higher-level analysis is now routed through the external AI adapter service instead of a local model runtime.
          </p>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <Card className="bg-[rgba(255,255,255,0.03)]">
              <CardContent className="p-5">
                <p className="text-sm font-semibold text-white">Current mode</p>
                <p className="mt-3 text-2xl font-bold text-white">{data.settings.model_mode}</p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">Persisted analysis mode used by the backend orchestration.</p>
              </CardContent>
            </Card>
            <Card className="bg-[rgba(255,255,255,0.03)]">
              <CardContent className="p-5">
                <p className="text-sm font-semibold text-white">Water interval</p>
                <p className="mt-3 text-2xl font-bold text-white">{data.settings.water_interval_min} min</p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">Reminder cadence already configured for hydration.</p>
              </CardContent>
            </Card>
            <Card className="bg-[rgba(255,255,255,0.03)]">
              <CardContent className="p-5">
                <p className="text-sm font-semibold text-white">Quiet hours</p>
                <p className="mt-3 text-2xl font-bold text-white">
                  {data.settings.quiet_hours_enabled ? 'Enabled' : 'Off'}
                </p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">Silence reminder delivery outside your preferred hours.</p>
              </CardContent>
            </Card>
          </div>
        </section>

        <section className="space-y-6">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Camera permission</CardTitle>
                <CardDescription className="mt-2">Grant access to your webcam to mirror the onboarding flow in the uploaded wireframes.</CardDescription>
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
                        No preview yet. Camera access is required before BADHABINOT can start a live session.
                      </p>
                    </div>
                  ) : null}
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button variant="secondary" iconLeft={<Camera className="size-4" />} onClick={requestCamera}>
                  {streamReady ? 'Refresh camera permission' : 'Grant camera access'}
                </Button>
                <Badge variant={readyToStart ? 'success' : 'warning'}>
                  {readyToStart ? 'Camera ready' : permissionState.toUpperCase()}
                </Badge>
              </div>
              {errorMessage ? <p className="text-sm text-[var(--danger)]">{errorMessage}</p> : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div>
                <CardTitle>Consent checklist</CardTitle>
                <CardDescription className="mt-2">These fields map directly to `PUT /api/v1/users/me/consents` and are required for the monitoring workflow.</CardDescription>
              </div>
            </CardHeader>
            <CardContent>
              <form
                className="space-y-4"
                onSubmit={handleSubmit((values) => {
                  if (!readyToStart) {
                    toast.error('Grant camera access before starting monitoring.')
                    return
                  }
                  completeMutation.mutate(values)
                })}
              >
                <div className="flex items-center justify-between gap-4 rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                  <div>
                    <p className="text-sm font-semibold text-white">Privacy policy accepted</p>
                    <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">Required to continue using the product.</p>
                  </div>
                  <Switch
                    checked={watch('privacy_policy_accepted')}
                    onCheckedChange={(checked) => setValue('privacy_policy_accepted', checked)}
                  />
                </div>
                {errors.privacy_policy_accepted ? <p className="text-sm text-[var(--danger)]">{errors.privacy_policy_accepted.message}</p> : null}

                <div className="flex items-center justify-between gap-4 rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                  <div>
                    <p className="text-sm font-semibold text-white">Camera monitoring accepted</p>
                    <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">Allows the live camera pipeline to process frames for immediate inference.</p>
                  </div>
                  <Switch
                    checked={watch('camera_monitoring_accepted')}
                    onCheckedChange={(checked) => setValue('camera_monitoring_accepted', checked)}
                  />
                </div>
                {errors.camera_monitoring_accepted ? <p className="text-sm text-[var(--danger)]">{errors.camera_monitoring_accepted.message}</p> : null}

                <div className="flex items-center justify-between gap-4 rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-white">Remote inference accepted</p>
                      <Lock className="size-4 text-[var(--text-muted)]" />
                    </div>
                    <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">
                      Required. Higher-level analysis is performed through the external AI adapter service.
                    </p>
                  </div>
                  <Switch
                    checked={watch('remote_inference_accepted')}
                    onCheckedChange={(checked) => setValue('remote_inference_accepted', checked)}
                  />
                </div>
                {errors.remote_inference_accepted ? <p className="text-sm text-[var(--danger)]">{errors.remote_inference_accepted.message}</p> : null}

                <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4 text-sm leading-6 text-[var(--text-muted)]">
                  Vision preprocessing stays local in the `vision-service`, but behavior interpretation is now external-API driven. Consent is required before the dashboard can analyze frames.
                </div>

                <Button className="w-full" size="lg" loading={completeMutation.isPending} iconLeft={<ChevronRight className="size-4" />} type="submit">
                  Accept and start secure monitoring
                </Button>
              </form>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  )
}
