import { useEffect } from 'react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import type { UpdateProfileRequest, UserContextResponse } from '@/types/user'

const profileSchema = z.object({
  display_name: z.string().min(2, 'Display name is required.').max(100),
  timezone: z.string().min(2, 'Timezone is required.').max(64),
  locale: z.string().min(2, 'Locale is required.').max(16),
})

type ProfileFormValues = z.infer<typeof profileSchema>

export function ProfileForm({
  user,
  isSaving,
  onSubmit,
}: {
  user: UserContextResponse
  isSaving: boolean
  onSubmit: (values: UpdateProfileRequest) => void
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      display_name: user.display_name,
      timezone: user.timezone,
      locale: user.locale,
    },
  })

  useEffect(() => {
    reset({
      display_name: user.display_name,
      timezone: user.timezone,
      locale: user.locale,
    })
  }, [reset, user])

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Profile</CardTitle>
          <CardDescription className="mt-2">Keep the account metadata used by monitoring summaries and session records current.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit(onSubmit)}>
          <Input label="Display name" error={errors.display_name?.message} {...register('display_name')} />
          <Input label="Timezone" error={errors.timezone?.message} {...register('timezone')} />
          <Input label="Locale" error={errors.locale?.message} {...register('locale')} />
          <div className="flex justify-end md:col-span-2">
            <Button type="submit" loading={isSaving} disabled={!isDirty}>
              Save profile
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}

