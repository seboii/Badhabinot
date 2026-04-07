import { useEffect } from 'react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useLanguage } from '@/i18n/language-provider'
import type { UpdateProfileRequest, UserContextResponse } from '@/types/user'

type ProfileFormValues = {
  display_name: string
  timezone: string
  locale: string
}

export function ProfileForm({
  user,
  isSaving,
  onSubmit,
}: {
  user: UserContextResponse
  isSaving: boolean
  onSubmit: (values: UpdateProfileRequest) => void
}) {
  const { isTurkish } = useLanguage()

  const profileSchema = z.object({
    display_name: z.string().min(2, isTurkish ? 'Gorunen ad zorunlu.' : 'Display name is required.').max(100),
    timezone: z.string().min(2, isTurkish ? 'Saat dilimi zorunlu.' : 'Timezone is required.').max(64),
    locale: z.string().min(2, isTurkish ? 'Dil formati zorunlu.' : 'Locale is required.').max(16),
  })

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
          <CardTitle>{isTurkish ? 'Profil' : 'Profile'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Izleme ozetleri ve oturum kayitlarinda kullanilan hesap metadatasini guncel tut.'
              : 'Keep the account metadata used by monitoring summaries and session records current.'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit(onSubmit)}>
          <Input label={isTurkish ? 'Gorunen ad' : 'Display name'} error={errors.display_name?.message} {...register('display_name')} />
          <Input label={isTurkish ? 'Saat dilimi' : 'Timezone'} error={errors.timezone?.message} {...register('timezone')} />
          <Input label={isTurkish ? 'Dil formati' : 'Locale'} error={errors.locale?.message} {...register('locale')} />
          <div className="flex justify-end md:col-span-2">
            <Button type="submit" loading={isSaving} disabled={!isDirty}>
              {isTurkish ? 'Profili kaydet' : 'Save profile'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
