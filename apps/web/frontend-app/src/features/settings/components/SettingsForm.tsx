import { useEffect } from 'react'
import { z } from 'zod'
import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import type { SettingsResponse } from '@/types/user'

const settingsSchema = z.object({
  sensitivity: z.enum(['LOW', 'MEDIUM', 'HIGH']),
  water_goal_ml: z.number().min(250).max(6000),
  water_interval_min: z.number().min(15).max(240),
  exercise_interval_min: z.number().min(15).max(240),
  quiet_hours_enabled: z.boolean(),
  quiet_hours_start: z.string().min(1),
  quiet_hours_end: z.string().min(1),
  model_mode: z.literal('API'),
  notifications_enabled: z.boolean(),
})

type SettingsFormValues = z.infer<typeof settingsSchema>

export function SettingsForm({
  settings,
  isSaving,
  onSubmit,
}: {
  settings: SettingsResponse
  isSaving: boolean
  onSubmit: (values: SettingsFormValues) => void
}) {
  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { isDirty },
  } = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: settings,
  })

  useEffect(() => {
    reset(settings)
  }, [reset, settings])

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Monitoring preferences</CardTitle>
          <CardDescription className="mt-2">Tune reminder cadence, sensitivity, quiet hours, notifications, and the API-based analysis workflow.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit(onSubmit)}>
          <input type="hidden" {...register('model_mode')} value="API" />

          <label className="flex flex-col gap-2">
            <span className="text-sm font-medium text-white">Sensitivity</span>
            <select
              className="h-12 rounded-2xl border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] px-4 text-sm text-white outline-none focus:border-[var(--primary)]"
              {...register('sensitivity')}
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </select>
          </label>

          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <p className="text-sm font-semibold text-white">Analysis mode</p>
            <p className="mt-2 text-sm text-[var(--text-muted)]">Higher-level analysis now runs through the external AI adapter service.</p>
            <p className="mt-4 text-lg font-semibold text-white">API</p>
          </div>

          <Input label="Daily water goal (ml)" type="number" min={250} max={6000} {...register('water_goal_ml', { valueAsNumber: true })} />
          <Input label="Water reminder interval (min)" type="number" min={15} max={240} {...register('water_interval_min', { valueAsNumber: true })} />
          <Input label="Break reminder interval (min)" type="number" min={15} max={240} {...register('exercise_interval_min', { valueAsNumber: true })} />
          <Input label="Quiet hours start" type="time" {...register('quiet_hours_start')} />
          <Input label="Quiet hours end" type="time" {...register('quiet_hours_end')} />

          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-white">Quiet hours</p>
                <p className="mt-1 text-sm text-[var(--text-muted)]">Pause reminders during the configured silent period.</p>
              </div>
              <Controller
                control={control}
                name="quiet_hours_enabled"
                render={({ field }) => <Switch checked={field.value} onCheckedChange={field.onChange} />}
              />
            </div>
          </div>

          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-white">Notifications</p>
                <p className="mt-1 text-sm text-[var(--text-muted)]">Keep desktop and in-app reminders active during monitoring.</p>
              </div>
              <Controller
                control={control}
                name="notifications_enabled"
                render={({ field }) => <Switch checked={field.value} onCheckedChange={field.onChange} />}
              />
            </div>
          </div>

          <div className="rounded-[24px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4 md:col-span-2">
            <p className="text-sm font-semibold text-white">Execution mode notes</p>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
              API-backed analysis requires remote inference consent in the privacy section below. Vision preprocessing still happens locally inside the vision-service.
            </p>
          </div>

          <div className="flex justify-end md:col-span-2">
            <Button type="submit" loading={isSaving} disabled={!isDirty}>
              Save preferences
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
