import { useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
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
import { useLanguage } from '@/i18n/language-provider'

type ResetPasswordFormValues = {
  newPassword: string
  confirmPassword: string
}

export function ResetPasswordPage() {
  const { isTurkish } = useLanguage()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      navigate('/forgot-password', { replace: true })
    }
  }, [token, navigate])

  const schema = z
    .object({
      newPassword: z
        .string()
        .min(8, isTurkish ? 'Sifre en az 8 karakter olmali.' : 'Password must be at least 8 characters.')
        .regex(
          /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
          isTurkish
            ? 'Şifre en az bir büyük harf, bir küçük harf ve bir rakam içermeli.'
            : 'Password must contain an uppercase letter, a lowercase letter, and a digit.',
        ),
      confirmPassword: z.string(),
    })
    .refine((data) => data.newPassword === data.confirmPassword, {
      message: isTurkish ? 'Sifreler eslesmiyor' : 'Passwords do not match',
      path: ['confirmPassword'],
    })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: authApi.confirmPasswordReset,
    onSuccess() {
      toast.success(
        isTurkish
          ? 'Sifreniz guncellendi. Giris yapabilirsiniz.'
          : 'Password updated. You can now sign in.',
      )
      navigate('/login', { replace: true })
    },
    onError(error) {
      toast.error(
        toErrorMessage(
          error,
          isTurkish
            ? 'Sifre sifirlanamadi. Baglanti gecersiz veya suresi dolmus olabilir.'
            : 'Password reset failed. The link may be invalid or expired.',
        ),
      )
    },
  })

  if (!token) return null

  return (
    <AuthShell
      title={isTurkish ? 'Yeni sifre belirle' : 'Set a new password'}
      subtitle={
        isTurkish ? 'Hesabiniz icin yeni bir sifre girin.' : 'Enter a new password for your account.'
      }
    >
      <form
        className="space-y-5"
        onSubmit={handleSubmit(({ newPassword }) =>
          mutation.mutate({ token: token, new_password: newPassword }),
        )}
      >
        <Input
          label={isTurkish ? 'Yeni sifre' : 'New password'}
          type="password"
          autoComplete="new-password"
          error={errors.newPassword?.message}
          {...register('newPassword')}
        />
        <Input
          label={isTurkish ? 'Sifre tekrar' : 'Confirm new password'}
          type="password"
          autoComplete="new-password"
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />
        <Button className="w-full" size="lg" loading={mutation.isPending} type="submit">
          {isTurkish ? 'Sifremi sifirla' : 'Reset password'}
        </Button>
      </form>
      <p className="mt-6 text-sm text-[var(--text-muted)]">
        <Link className="font-semibold text-white" to="/login">
          {isTurkish ? 'Girise don' : 'Back to sign in'}
        </Link>
      </p>
    </AuthShell>
  )
}
