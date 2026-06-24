import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import { ChevronLeft, ChevronRight, CheckCircle } from 'lucide-react'
import { authApi } from '@/api/auth'
import { userApi } from '@/api/user'
import { toErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { CaptchaWidget } from '@/components/ui/captcha-widget'
import { AuthShell } from '@/features/auth/components/AuthShell'
import { KvkkModal } from '@/features/auth/KvkkModal'
import { FaceRegistrationStep } from '@/features/auth/FaceRegistrationStep'
import { useAuth } from '@/hooks/use-auth'
import { useLanguage } from '@/i18n/language-provider'
import { useUserStore } from '@/store/user-store'

type RegisterStep = 'account_info' | 'consents' | 'camera_face'

type AccountInfoValues = {
  email: string
  password: string
  confirmPassword: string
  display_name: string
  timezone: string
  locale: string
}

type ConsentsValues = {
  privacy_policy_accepted: boolean
  camera_monitoring_accepted: boolean
  remote_inference_accepted: boolean
}

export function RegisterPage() {
  const { isTurkish } = useLanguage()
  const navigate = useNavigate()
  const { setSession } = useAuth()
  const setProfile = useUserStore((s) => s.setProfile)

  const [step, setStep] = useState<RegisterStep>('account_info')
  const [accountData, setAccountData] = useState<AccountInfoValues | null>(null)
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const [consents, setConsents] = useState<ConsentsValues>({
    privacy_policy_accepted: false,
    camera_monitoring_accepted: false,
    remote_inference_accepted: false,
  })
  const [kvkkOpen, setKvkkOpen] = useState(false)

  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Europe/Istanbul'
  const locale = navigator.language || 'tr-TR'

  const accountSchema = z
    .object({
      email: z.email(isTurkish ? 'Geçerli bir e-posta adresi gir.' : 'Enter a valid email address.'),
      password: z
        .string()
        .min(8, isTurkish ? 'Şifre en az 8 karakter olmalı.' : 'Password must be at least 8 characters.')
        .regex(
          /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
          isTurkish
            ? 'Şifre en az bir büyük harf, bir küçük harf ve bir rakam içermeli.'
            : 'Password must contain an uppercase letter, a lowercase letter, and a digit.',
        ),
      confirmPassword: z.string(),
      display_name: z.string().min(2, isTurkish ? 'Ad zorunlu.' : 'Name is required.').max(100),
      timezone: z.string().min(2).max(64),
      locale: z.string().min(2).max(16),
    })
    .refine((d) => d.password === d.confirmPassword, {
      message: isTurkish ? 'Şifreler eşleşmiyor' : 'Passwords do not match',
      path: ['confirmPassword'],
    })

  const { register, handleSubmit, formState: { errors } } = useForm<AccountInfoValues>({
    resolver: zodResolver(accountSchema),
    defaultValues: { timezone, locale },
  })

  // Called at the end of step 2 — registers + saves consents
  const completeMutation = useMutation({
    mutationFn: async () => {
      if (!accountData) throw new Error('Missing account data')
      if (!captchaToken) throw new Error('Missing captcha token')
      const { confirmPassword: _, ...rest } = accountData
      return authApi.register({ ...rest, captcha_token: captchaToken })
    },
    onSuccess(result) {
      // Yeni kayıtlar yönetici onayı bekler — token gelmez. Onam + yüz kaydı,
      // onaydan sonraki ilk girişte /onboarding akışında toplanır.
      if (result.pending_approval || !result.session) {
        toast.success(
          result.message ||
            (isTurkish
              ? 'Hesabınız oluşturuldu. Yönetici onayından sonra giriş yapabilirsiniz.'
              : 'Account created. You can sign in after an administrator approves it.'),
        )
        navigate('/login')
        return
      }
      // (İleride otomatik onay açılırsa) oturumu kur ve devam et.
      setSession(result.session)
      void userApi.updateConsents(consents).catch(() => {})
      void userApi.getMe().then(setProfile).catch(() => {})
      setStep('camera_face')
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Kayıt başarısız.' : 'Registration failed.'))
    },
  })

  const allConsentsGiven =
    consents.privacy_policy_accepted &&
    consents.camera_monitoring_accepted &&
    consents.remote_inference_accepted

  function onAccountNext(values: AccountInfoValues) {
    if (!captchaToken) {
      toast.error(isTurkish ? 'Lütfen doğrulama sorusunu cevaplayın.' : 'Please complete the verification.')
      return
    }
    setAccountData(values)
    setStep('consents')
  }

  function handleFaceComplete(skipped: boolean) {
    if (skipped) {
      toast.info(
        isTurkish
          ? 'Yüz kaydı atlandı. Ayarlardan daha sonra yapabilirsiniz.'
          : 'Face registration skipped. You can do it later from Settings.',
      )
    }
    navigate('/dashboard', { replace: true })
  }

  // ────────────────────────────────────────────────────
  // Step 1: Account Info
  // ────────────────────────────────────────────────────
  if (step === 'account_info') {
    return (
      <AuthShell
        title={isTurkish ? 'Hesap Oluştur' : 'Create your account'}
        subtitle={
          isTurkish
            ? 'Adım 1 / 3 — Hesap bilgilerinizi girin.'
            : 'Step 1 / 3 — Enter your account details.'
        }
      >
        <form className="space-y-4" onSubmit={handleSubmit(onAccountNext)}>
          <Input
            label={isTurkish ? 'Ad Soyad' : 'Full name'}
            autoComplete="name"
            error={errors.display_name?.message}
            {...register('display_name')}
          />
          <Input
            label={isTurkish ? 'E-posta' : 'Email'}
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />
          <Input
            label={isTurkish ? 'Şifre' : 'Password'}
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register('password')}
          />
          <Input
            label={isTurkish ? 'Şifre tekrar' : 'Confirm password'}
            type="password"
            autoComplete="new-password"
            error={errors.confirmPassword?.message}
            {...register('confirmPassword')}
          />
          <input type="hidden" {...register('timezone')} />
          <input type="hidden" {...register('locale')} />
          <CaptchaWidget
            isTurkish={isTurkish}
            onVerified={setCaptchaToken}
            onReset={() => setCaptchaToken(null)}
          />
          <Button
            className="w-full"
            size="lg"
            disabled={!captchaToken}
            type="submit"
            iconLeft={<ChevronRight className="size-4" />}
          >
            {isTurkish ? 'Sonraki Adım' : 'Next Step'}
          </Button>
        </form>
        <p className="mt-6 text-sm text-[var(--text-muted)]">
          {isTurkish ? 'Zaten hesabın var mı?' : 'Already have an account?'}{' '}
          <Link className="font-semibold text-white" to="/login">
            {isTurkish ? 'Giriş yap' : 'Sign in'}
          </Link>
        </p>
      </AuthShell>
    )
  }

  // ────────────────────────────────────────────────────
  // Step 2: Consents + KVKK
  // ────────────────────────────────────────────────────
  if (step === 'consents') {
    return (
      <AuthShell
        title={isTurkish ? 'İzinler ve KVKK' : 'Consents & Privacy'}
        subtitle={
          isTurkish
            ? 'Adım 2 / 3 — Platforma erişmek için aşağıdaki izinleri onaylayın.'
            : 'Step 2 / 3 — Accept the following permissions to use the platform.'
        }
      >
        <div className="space-y-4">
          {/* KVKK Checkbox */}
          <ConsentRow
            checked={consents.privacy_policy_accepted}
            title={isTurkish ? 'KVKK Aydınlatma Metni' : 'Data Protection Disclosure'}
            description={
              isTurkish
                ? 'Metni okuduktan sonra onaylanabilir.'
                : 'Can be accepted after reading the full text.'
            }
            onChange={(checked) =>
              setConsents((p) => ({ ...p, privacy_policy_accepted: checked }))
            }
            actionLabel={
              consents.privacy_policy_accepted
                ? undefined
                : isTurkish ? 'Metni Oku' : 'Read Text'
            }
            onAction={() => setKvkkOpen(true)}
          />

          {/* Camera monitoring */}
          <ConsentRow
            checked={consents.camera_monitoring_accepted}
            title={isTurkish ? 'Kamera İzleme Onayı' : 'Camera Monitoring Consent'}
            description={
              isTurkish
                ? 'Canlı kamera kareleri anlık çıkarım için işlenir.'
                : 'Live camera frames are processed for real-time inference.'
            }
            onChange={(checked) =>
              setConsents((p) => ({ ...p, camera_monitoring_accepted: checked }))
            }
          />

          {/* Remote inference */}
          <ConsentRow
            checked={consents.remote_inference_accepted}
            title={isTurkish ? 'Uzak Çıkarım Onayı' : 'Remote Inference Consent'}
            description={
              isTurkish
                ? 'Üst seviye analiz harici AI bağdaştırıcı servisinde yapılır.'
                : 'Higher-level analysis is performed through the external AI adapter service.'
            }
            onChange={(checked) =>
              setConsents((p) => ({ ...p, remote_inference_accepted: checked }))
            }
          />

          <div className="flex gap-3 pt-2">
            <Button
              variant="secondary"
              iconLeft={<ChevronLeft className="size-4" />}
              onClick={() => setStep('account_info')}
            >
              {isTurkish ? 'Geri' : 'Back'}
            </Button>
            <Button
              variant="primary"
              className="flex-1"
              disabled={!allConsentsGiven || completeMutation.isPending}
              loading={completeMutation.isPending}
              iconLeft={<ChevronRight className="size-4" />}
              onClick={() => completeMutation.mutate()}
            >
              {isTurkish ? 'Hesap Oluştur' : 'Create Account'}
            </Button>
          </div>
        </div>

        <KvkkModal
          isOpen={kvkkOpen}
          onClose={() => setKvkkOpen(false)}
          onConfirm={() => {
            setKvkkOpen(false)
            setConsents((p) => ({ ...p, privacy_policy_accepted: true }))
          }}
        />
      </AuthShell>
    )
  }

  // ────────────────────────────────────────────────────
  // Step 3: Camera + Face Registration
  // ────────────────────────────────────────────────────
  return (
    <AuthShell
      title={isTurkish ? 'Yüz Kaydı' : 'Face Registration'}
      subtitle={
        isTurkish
          ? 'Adım 3 / 3 — Yüz tanıma için kayıt yapın veya atlayın.'
          : 'Step 3 / 3 — Register your face for recognition or skip.'
      }
    >
      <FaceRegistrationStep onComplete={handleFaceComplete} />
    </AuthShell>
  )
}

// ────────────────────────────────────────────────────
// ConsentRow helper
// ────────────────────────────────────────────────────

type ConsentRowProps = {
  checked: boolean
  title: string
  description: string
  onChange: (checked: boolean) => void
  actionLabel?: string
  onAction?: () => void
}

function ConsentRow({ checked, title, description, onChange, actionLabel, onAction }: ConsentRowProps) {
  return (
    <div className="flex items-start gap-3 rounded-[20px] border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
      <button
        type="button"
        className={`mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-md border-2 transition ${
          checked
            ? 'border-[var(--primary)] bg-[var(--primary)]'
            : 'border-[var(--line-soft)] bg-transparent'
        }`}
        onClick={() => onChange(!checked)}
        aria-checked={checked}
        role="checkbox"
      >
        {checked && <CheckCircle className="size-3.5 text-white" />}
      </button>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white">{title}</p>
        <p className="mt-1 text-sm leading-5 text-[var(--text-muted)]">{description}</p>
        {actionLabel && onAction && (
          <button
            type="button"
            className="mt-2 text-xs font-semibold text-[var(--primary)] underline underline-offset-2 transition hover:opacity-80"
            onClick={onAction}
          >
            {actionLabel}
          </button>
        )}
      </div>
    </div>
  )
}
