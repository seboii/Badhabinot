import { useMemo } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
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
import { useLanguage } from '@/i18n/language-provider'

type LoginFormValues = {
  email: string
  password: string
}

export function LoginPage() {
  const { isTurkish } = useLanguage()
  const navigate = useNavigate()
  const location = useLocation()
  const { setSession } = useAuth()
  const from = useMemo(() => {
    const state = location.state as { from?: string } | null
    return state?.from || '/'
  }, [location.state])

  const loginSchema = z.object({
    email: z.email(isTurkish ? 'Gecerli bir e-posta adresi gir.' : 'Enter a valid email address.'),
    password: z.string().min(8, isTurkish ? 'Sifre en az 8 karakter olmali.' : 'Password must be at least 8 characters.'),
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  })

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess(session) {
      setSession(session)
      toast.success(isTurkish ? 'BADHABINOT hos geldin.' : 'Welcome back to BADHABINOT.')
      navigate(from, { replace: true })
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Giris basarisiz.' : 'Login failed.'))
    },
  })

  return (
    <AuthShell
      title={isTurkish ? 'Devam etmek icin giris yap' : 'Sign in to continue'}
      subtitle={
        isTurkish
          ? 'Izleme oturumlarini surdur, gecmisi incele ve gizlilik odakli davranis takibini yonet.'
          : 'Resume monitoring sessions, review your history, and manage privacy-focused behavior tracking.'
      }
    >
      <form className="space-y-5" onSubmit={handleSubmit((values) => loginMutation.mutate(values))}>
        <Input
          label={isTurkish ? 'E-posta' : 'Email'}
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register('email')}
        />
        <Input
          label={isTurkish ? 'Sifre' : 'Password'}
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        <Button className="w-full" size="lg" loading={loginMutation.isPending} type="submit">
          {isTurkish ? 'Giris yap' : 'Sign in'}
        </Button>
      </form>
      <p className="mt-6 text-sm text-[var(--text-muted)]">
        {isTurkish ? 'Hesabin yok mu?' : 'Need an account?'}{' '}
        <Link className="font-semibold text-white" to="/register">
          {isTurkish ? 'Hesap olustur' : 'Create one'}
        </Link>
      </p>
    </AuthShell>
  )
}
