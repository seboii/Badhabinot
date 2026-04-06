import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import { authApi } from '@/api/auth'
import { toErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { AuthShell } from '@/features/auth/components/AuthShell'
import { useAuth } from '@/hooks/use-auth'

const registerSchema = z.object({
  email: z.email('Enter a valid email address.'),
  password: z.string().min(8, 'Password must be at least 8 characters.'),
  display_name: z.string().min(2, 'Display name is required.').max(100),
  timezone: z.string().min(2, 'Timezone is required.').max(64),
  locale: z.string().min(2, 'Locale is required.').max(16),
})

type RegisterFormValues = z.infer<typeof registerSchema>

export function RegisterPage() {
  const navigate = useNavigate()
  const { setSession } = useAuth()

  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Istanbul'
  const locale = navigator.language || 'en-US'

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
      toast.success('Account created. Complete onboarding to start monitoring.')
      navigate('/', { replace: true })
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Registration failed.'))
    },
  })

  return (
    <AuthShell
      title="Create your BADHABINOT account"
      subtitle="Start with a secure profile, then configure monitoring consent, camera access, and live analysis preferences."
    >
      <form className="grid gap-5 md:grid-cols-2" onSubmit={handleSubmit((values) => registerMutation.mutate(values))}>
        <div className="md:col-span-2">
          <Input label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register('email')} />
        </div>
        <div className="md:col-span-2">
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register('password')}
          />
        </div>
        <Input label="Display name" error={errors.display_name?.message} {...register('display_name')} />
        <Input label="Timezone" error={errors.timezone?.message} {...register('timezone')} />
        <Input label="Locale" error={errors.locale?.message} {...register('locale')} />
        <div className="md:col-span-2">
          <Button className="w-full" size="lg" loading={registerMutation.isPending} type="submit">
            Create account
          </Button>
        </div>
      </form>
      <p className="mt-6 text-sm text-[var(--text-muted)]">
        Already registered?{' '}
        <Link className="font-semibold text-white" to="/login">
          Sign in
        </Link>
      </p>
    </AuthShell>
  )
}
