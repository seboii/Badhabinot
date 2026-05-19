import { useState } from 'react'
import { Link } from 'react-router-dom'
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

type ForgotPasswordFormValues = {
  email: string
}

export function ForgotPasswordPage() {
  const { isTurkish } = useLanguage()
  const [submitted, setSubmitted] = useState(false)

  const schema = z.object({
    email: z.email(isTurkish ? 'Gecerli bir e-posta adresi gir.' : 'Enter a valid email address.'),
  })

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: authApi.requestPasswordReset,
    onSuccess() {
      setSubmitted(true)
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Istek gonderilemedi.' : 'Request could not be sent.'))
    },
  })

  return (
    <AuthShell
      title={isTurkish ? 'Sifreni sifirla' : 'Reset your password'}
      subtitle={
        isTurkish
          ? 'Kayitli e-posta adresini gir, sifre sifirlama baglantiyi gondecelim.'
          : "Enter your registered email address and we'll send you a reset link."
      }
    >
      {submitted ? (
        <div className="rounded-2xl border border-[var(--line-soft)] bg-[var(--surface-soft)] p-6">
          <p className="font-semibold text-[var(--text-strong)]">
            {isTurkish ? 'Baglanti gonderildi' : 'Link sent'}
          </p>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            {isTurkish
              ? 'Sifre sifirlama baglantisi e-posta adresinize gonderildi. Gelen kutunuzu kontrol edin.'
              : 'A password reset link has been sent to your email address. Check your inbox.'}
          </p>
        </div>
      ) : (
        <form className="space-y-5" onSubmit={handleSubmit((values) => mutation.mutate(values))}>
          <Input
            label={isTurkish ? 'E-posta' : 'Email'}
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />
          <Button className="w-full" size="lg" loading={mutation.isPending} type="submit">
            {isTurkish ? 'Sifirlama baglantisi gonder' : 'Send reset link'}
          </Button>
        </form>
      )}
      <p className="mt-6 text-sm text-[var(--text-muted)]">
        <Link className="font-semibold text-white" to="/login">
          {isTurkish ? 'Girise don' : 'Back to sign in'}
        </Link>
      </p>
    </AuthShell>
  )
}
