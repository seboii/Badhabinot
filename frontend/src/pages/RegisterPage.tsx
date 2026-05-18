import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import { authApi } from '@/api/auth'
import { userApi } from '@/api/user'
import { toErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { CaptchaWidget } from '@/components/ui/captcha-widget'
import { AuthShell } from '@/features/auth/components/AuthShell'
import { useAuth } from '@/hooks/use-auth'
import { useLanguage } from '@/i18n/language-provider'
import { useUserStore } from '@/store/user-store'

type RegisterFormValues = {
  email: string
  password: string
  confirmPassword: string
  display_name: string
  timezone: string
  locale: string
}

export function RegisterPage() {
  const { isTurkish } = useLanguage()
  const navigate = useNavigate()
  const { setSession } = useAuth()
  const setProfile = useUserStore((s) => s.setProfile)
  const [captchaValid, setCaptchaValid] = useState(false)

  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Istanbul'
  const locale = navigator.language || 'en-US'

  const registerSchema = z
    .object({
      email: z.email(isTurkish ? 'Gecerli bir e-posta adresi gir.' : 'Enter a valid email address.'),
      password: z.string().min(8, isTurkish ? 'Sifre en az 8 karakter olmali.' : 'Password must be at least 8 characters.'),
      confirmPassword: z.string(),
      display_name: z.string().min(2, isTurkish ? 'Gorunen ad zorunlu.' : 'Display name is required.').max(100),
      timezone: z.string().min(2, isTurkish ? 'Saat dilimi zorunlu.' : 'Timezone is required.').max(64),
      locale: z.string().min(2, isTurkish ? 'Dil formati zorunlu.' : 'Locale is required.').max(16),
    })
    .refine((data) => data.confirmPassword === data.password, {
      message: isTurkish ? 'Sifreler eslesmiyor' : 'Passwords do not match',
      path: ['confirmPassword'],
    })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      timezone,
      locale,
    },
  })

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess(session) {
      setSession(session)
      // Eagerly populate user store so protected pages have instant data
      void userApi.getMe().then(setProfile).catch(() => { /* AppShell will sync on navigation */ })
      toast.success(
        isTurkish ? 'Hesap olusturuldu. Izlemeyi baslatmak icin baslangici tamamla.' : 'Account created. Complete onboarding to start monitoring.',
      )
      navigate('/', { replace: true })
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Kayit basarisiz.' : 'Registration failed.'))
    },
  })

  function onSubmit({ confirmPassword: _, ...values }: RegisterFormValues) {
    if (!captchaValid) {
      toast.error(isTurkish ? 'Lütfen doğrulama sorusunu cevaplayın.' : 'Please complete the verification.')
      return
    }
    registerMutation.mutate(values)
  }

  return (
    <AuthShell
      title={isTurkish ? 'BADHABINOT hesabi olustur' : 'Create your BADHABINOT account'}
      subtitle={
        isTurkish
          ? 'Guvenli bir profil ile basla, sonra izleme izni, kamera erisimi ve canli analiz tercihlerini ayarla.'
          : 'Start with a secure profile, then configure monitoring consent, camera access, and live analysis preferences.'
      }
    >
      <form className="grid gap-5 md:grid-cols-2" onSubmit={handleSubmit(onSubmit)}>
        <div className="md:col-span-2">
          <Input
            label={isTurkish ? 'E-posta' : 'Email'}
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />
        </div>
        <div className="md:col-span-2">
          <Input
            label={isTurkish ? 'Sifre' : 'Password'}
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register('password')}
          />
        </div>
        <div className="md:col-span-2">
          <Input
            label={isTurkish ? 'Sifre tekrar' : 'Confirm password'}
            type="password"
            autoComplete="new-password"
            error={errors.confirmPassword?.message}
            {...register('confirmPassword')}
          />
        </div>
        <Input label={isTurkish ? 'Gorunen ad' : 'Display name'} error={errors.display_name?.message} {...register('display_name')} />
        <Input label={isTurkish ? 'Saat dilimi' : 'Timezone'} error={errors.timezone?.message} {...register('timezone')} />
        <Input label={isTurkish ? 'Dil formati' : 'Locale'} error={errors.locale?.message} {...register('locale')} />
        <div className="md:col-span-2">
          <CaptchaWidget isTurkish={isTurkish} onValidate={setCaptchaValid} />
        </div>
        <div className="md:col-span-2">
          <Button className="w-full" size="lg" loading={registerMutation.isPending} disabled={!captchaValid} type="submit">
            {isTurkish ? 'Hesap olustur' : 'Create account'}
          </Button>
        </div>
      </form>
      <p className="mt-6 text-sm text-[var(--text-muted)]">
        {isTurkish ? 'Zaten kayitli misin?' : 'Already registered?'}{' '}
        <Link className="font-semibold text-white" to="/login">
          {isTurkish ? 'Giris yap' : 'Sign in'}
        </Link>
      </p>
    </AuthShell>
  )
}
