import { useEffect } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { useLanguage } from '@/i18n/language-provider'
import type { ConsentResponse, UpdateConsentsRequest } from '@/types/user'

const consentSchema = z.object({
  privacy_policy_accepted: z.boolean(),
  camera_monitoring_accepted: z.boolean(),
  remote_inference_accepted: z.boolean(),
})

type ConsentFormValues = z.infer<typeof consentSchema>

export function ConsentForm({
  consents,
  isSaving,
  onSubmit,
}: {
  consents: ConsentResponse
  isSaving: boolean
  onSubmit: (values: UpdateConsentsRequest) => void
}) {
  const { isTurkish } = useLanguage()
  const consentLabels = [
    {
      key: 'privacy_policy_accepted' as const,
      title: isTurkish ? 'Gizlilik politikasi onayi' : 'Privacy policy acceptance',
      description: isTurkish
        ? 'Izleme, panel ve gecmis akislarini kullanmaya devam etmek icin zorunlu.'
        : 'Required to keep using monitoring, dashboard, and history workflows.',
    },
    {
      key: 'camera_monitoring_accepted' as const,
      title: isTurkish ? 'Kamera izleme onayi' : 'Camera monitoring consent',
      description: isTurkish
        ? 'Canli web kamera analizi ve oturum destekli izleme icin zorunlu.'
        : 'Required for live webcam analysis and session-backed monitoring.',
    },
    {
      key: 'remote_inference_accepted' as const,
      title: isTurkish ? 'Uzak cikarim onayi' : 'Remote inference consent',
      description: isTurkish
        ? 'Vision-service cikisini yorumlayan harici AI analiz hatti icin zorunlu.'
        : 'Required for the external AI analysis pipeline that interprets the vision-service output.',
    },
  ]

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
          <CardTitle>{isTurkish ? 'Gizlilik ve onay' : 'Privacy and consent'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Bu anahtarlar arka uc ve izleme orkestrasyonunun kullandigi kalici onay modelini dogrudan gunceller.'
              : 'These switches directly update the persisted consent model used by the backend and monitoring orchestration.'}
          </CardDescription>
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

          {!remoteInferenceAccepted ? (
            <div className="rounded-[24px] border border-[rgba(245,158,11,0.35)] bg-[rgba(245,158,11,0.08)] p-4 text-sm leading-6 text-[#ffd999]">
              {isTurkish
                ? 'Uzak cikarim onayi acilana kadar kare analizi kapali. Kamera onizlemesi ve oturum kontrolleri acik kalabilir, fakat arka uc gorsel analiz isteklerini reddeder.'
                : 'Frame analysis is disabled until remote inference consent is enabled. Camera preview and session controls can stay available, but the backend will reject image analysis requests.'}
            </div>
          ) : null}

          <div className="flex justify-end">
            <Button type="submit" loading={isSaving} disabled={!isDirty}>
              {isTurkish ? 'Onaylari kaydet' : 'Save consents'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
