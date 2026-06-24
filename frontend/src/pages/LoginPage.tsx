import { useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import { ScanFace, KeyRound } from 'lucide-react'
import { authApi } from '@/api/auth'
import { userApi } from '@/api/user'
import { toErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { CaptchaWidget } from '@/components/ui/captcha-widget'
import { AuthShell } from '@/features/auth/components/AuthShell'
import { FaceLoginTab } from '@/features/auth/FaceLoginTab'
import { useAuth } from '@/hooks/use-auth'
import { useLanguage } from '@/i18n/language-provider'
import { useUserStore } from '@/store/user-store'
import type { TokenResponse } from '@/types/auth'

type LoginMode = 'face' | 'password'

type PasswordFormValues = {
  email: string
  password: string
}

export function LoginPage() {
  const { isTurkish } = useLanguage()
  const navigate = useNavigate()
  const location = useLocation()
  const { setSession } = useAuth()
  const setProfile = useUserStore((s) => s.setProfile)
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const [mode, setMode] = useState<LoginMode>('face')
  const [prefillEmail, setPrefillEmail] = useState('')

  const from = useMemo(() => {
    const state = location.state as { from?: string } | null
    return state?.from || '/'
  }, [location.state])

  const passwordSchema = z.object({
    email: z.email(isTurkish ? 'Geçerli bir e-posta adresi gir.' : 'Enter a valid email address.'),
    password: z.string().min(8, isTurkish ? 'Şifre en az 8 karakter olmalı.' : 'Password must be at least 8 characters.'),
  })

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { email: prefillEmail },
  })

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: handleLoginSuccess,
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Giriş başarısız.' : 'Login failed.'))
    },
  })

  function handleLoginSuccess(session: TokenResponse) {
    setSession(session)
    void userApi.getMe().then(setProfile).catch(() => {})
    toast.success(isTurkish ? 'BADHABINOT hoş geldin.' : 'Welcome back to BADHABINOT.')
    navigate(from, { replace: true })
  }

  function switchToPassword(email: string) {
    setPrefillEmail(email)
    setValue('email', email)
    setMode('password')
  }

  function onPasswordSubmit(values: PasswordFormValues) {
    if (!captchaToken) {
      toast.error(isTurkish ? 'Lütfen doğrulama sorusunu cevaplayın.' : 'Please complete the verification.')
      return
    }
    loginMutation.mutate(values)
  }

  return (
    <AuthShell
      title={isTurkish ? 'Giriş Yap' : 'Sign in'}
      subtitle={
        isTurkish
          ? 'Yüz tanıma veya şifre ile güvenli erişim.'
          : 'Secure access via face recognition or password.'
      }
    >
      {/* Tab switcher */}
      <div className="mb-6 flex rounded-[18px] border border-[var(--line-soft)] bg-[var(--surface-subtle)] p-1">
        <TabButton
          active={mode === 'face'}
          onClick={() => setMode('face')}
          icon={<ScanFace className="size-4" />}
          label={isTurkish ? 'Yüz ile Giriş' : 'Face Login'}
        />
        <TabButton
          active={mode === 'password'}
          onClick={() => setMode('password')}
          icon={<KeyRound className="size-4" />}
          label={isTurkish ? 'Şifre ile Giriş' : 'Password Login'}
        />
      </div>

      {/* Face login tab */}
      {mode === 'face' && (
        <FaceLoginTab
          onSuccess={handleLoginSuccess}
          onSwitchToPassword={switchToPassword}
        />
      )}

      {/* Password login tab */}
      {mode === 'password' && (
        <form className="space-y-5" onSubmit={handleSubmit(onPasswordSubmit)}>
          <Input
            label={isTurkish ? 'E-posta' : 'Email'}
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />
          <div>
            <Input
              label={isTurkish ? 'Şifre' : 'Password'}
              type="password"
              autoComplete="current-password"
              error={errors.password?.message}
              {...register('password')}
            />
            <div className="mt-2 flex justify-end">
              <Link className="text-sm font-semibold text-white" to="/forgot-password">
                {isTurkish ? 'Şifremi unuttum' : 'Forgot password?'}
              </Link>
            </div>
          </div>
          <CaptchaWidget
            isTurkish={isTurkish}
            onVerified={setCaptchaToken}
            onReset={() => setCaptchaToken(null)}
          />
          <Button
            className="w-full"
            size="lg"
            loading={loginMutation.isPending}
            disabled={!captchaToken}
            type="submit"
          >
            {isTurkish ? 'Giriş yap' : 'Sign in'}
          </Button>
        </form>
      )}

      <p className="mt-6 text-sm text-[var(--text-muted)]">
        {isTurkish ? 'Hesabın yok mu?' : 'Need an account?'}{' '}
        <Link className="font-semibold text-white" to="/register">
          {isTurkish ? 'Hesap oluştur' : 'Create one'}
        </Link>
      </p>
    </AuthShell>
  )
}

// ────────────────────────────────────────────────────
// TabButton helper
// ────────────────────────────────────────────────────

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex flex-1 items-center justify-center gap-2 rounded-[14px] px-3 py-2 text-sm font-medium transition ${
        active
          ? 'bg-[var(--surface-soft)] text-white shadow-sm'
          : 'text-[var(--text-muted)] hover:text-[var(--text-strong)]'
      }`}
    >
      {icon}
      {label}
    </button>
  )
}
