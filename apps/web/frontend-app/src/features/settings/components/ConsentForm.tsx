import { useEffect } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import type { ConsentResponse, ModelMode, UpdateConsentsRequest } from '@/types/user'

const consentSchema = z.object({
  privacy_policy_accepted: z.boolean(),
  camera_monitoring_accepted: z.boolean(),
  remote_inference_accepted: z.boolean(),
})

type ConsentFormValues = z.infer<typeof consentSchema>

const consentLabels = [
  {
    key: 'privacy_policy_accepted' as const,
    title: 'Privacy policy acceptance',
    description: 'Required to keep using monitoring, dashboard, and history workflows.',
  },
  {
    key: 'camera_monitoring_accepted' as const,
    title: 'Camera monitoring consent',
    description: 'Required for live webcam analysis and session-backed monitoring.',
  },
  {
    key: 'remote_inference_accepted' as const,
    title: 'Remote inference consent',
    description: 'Enable only if you intentionally switch to API-backed inference mode.',
  },
]

export function ConsentForm({
  consents,
  modelMode,
  isSaving,
  onSubmit,
}: {
  consents: ConsentResponse
  modelMode: ModelMode
  isSaving: boolean
  onSubmit: (values: UpdateConsentsRequest) => void
}) {
  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
    watch,
  } = useForm<ConsentFormValues>({
    resolver: zodResolver(consentSchema),
    defaultValues: consents,
  })

  useEffect(() => {
    reset(consents)
  }, [consents, reset])

  const remoteInferenceAccepted = watch('remote_inference_accepted')

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Privacy and consent</CardTitle>
          <CardDescription className="mt-2">These switches directly update the persisted consent model used by the backend and monitoring orchestration.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          {consentLabels.map((item) => (
            <div key={item.key} className="flex items-center justify-between gap-4 rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
              <div>
                <p className="text-sm font-semibold text-white">{item.title}</p>
                <p className="mt-1 text-sm leading-6 text-[var(--text-muted)]">{item.description}</p>
              </div>
              <Controller
                control={control}
                name={item.key}
                render={({ field }) => <Switch checked={field.value} onCheckedChange={field.onChange} />}
              />
            </div>
          ))}

          {modelMode === 'API' && !remoteInferenceAccepted ? (
            <div className="rounded-[24px] border border-[rgba(245,158,11,0.35)] bg-[rgba(245,158,11,0.08)] p-4 text-sm leading-6 text-[#ffd999]">
              API mode is selected in preferences, but remote inference consent is still disabled. The backend will keep signaling local-only privacy posture until this consent is enabled.
            </div>
          ) : null}

          <div className="flex justify-end">
            <Button type="submit" loading={isSaving} disabled={!isDirty}>
              Save consents
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
