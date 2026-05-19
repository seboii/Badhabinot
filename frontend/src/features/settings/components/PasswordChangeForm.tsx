import type { InputHTMLAttributes } from 'react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { userApi } from '@/api/user'
import { toErrorMessage } from '@/api/client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/cn'
import { useLanguage } from '@/i18n/language-provider'

// Local helper — same visual style as the existing Input component, adds eye toggle.
function PasswordField({
  label,
  error,
  className,
  ...inputProps
}: InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string }) {
  const [visible, setVisible] = useState(false)

  return (
    <label className="flex flex-col gap-2">
      <span className="text-sm font-medium text-[var(--text-strong)]">{label}</span>
      <div className="relative">
        <input
          {...inputProps}
          type={visible ? 'text' : 'password'}
          className={cn(
            'h-12 w-full rounded-2xl border border-[var(--line-soft)] bg-[var(--surface-subtle)] px-4 pr-12 text-sm text-[var(--text-strong)] outline-none transition placeholder:text-[var(--text-soft)] focus:border-[var(--primary)] focus:bg-[var(--surface-soft)]',
            error && 'border-[var(--danger)]',
            className,
          )}
        />
        <button
          type="button"
          tabIndex={-1}
          onClick={() => setVisible((v) => !v)}
          className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--text-soft)] hover:text-[var(--text-strong)]"
        >
          {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
        </button>
      </div>
      {error ? <span className="text-xs text-[var(--danger)]">{error}</span> : null}
    </label>
  )
}

type ChangePasswordFormValues = {
  currentPassword: string
  newPassword: string
  confirmNewPassword: string
}

export function PasswordChangeForm() {
  const { isTurkish } = useLanguage()

  const schema = z
    .object({
      currentPassword: z.string().min(1, isTurkish ? 'Mevcut sifre zorunlu.' : 'Current password is required.'),
      newPassword: z
        .string()
        .min(8, isTurkish ? 'Yeni sifre en az 8 karakter olmali.' : 'New password must be at least 8 characters.'),
      confirmNewPassword: z.string(),
    })
    .refine((data) => data.newPassword === data.confirmNewPassword, {
      message: isTurkish ? 'Sifreler eslesmiyor' : 'Passwords do not match',
      path: ['confirmNewPassword'],
    })

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: userApi.changePassword,
    onSuccess() {
      toast.success(isTurkish ? 'Şifreniz başarıyla güncellendi' : 'Password successfully updated.')
      reset()
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Sifre guncellenemedi.' : 'Unable to update password.'))
    },
  })

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{isTurkish ? 'Şifre Değiştir' : 'Change password'}</CardTitle>
          <CardDescription className="mt-2">
            {isTurkish
              ? 'Mevcut sifrenizi girerek yeni bir sifre belirleyin. Tum aktif oturumlar sonlandirilir.'
              : 'Confirm your current password then set a new one. All active sessions will be invalidated.'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <form
          className="grid gap-4 md:grid-cols-2"
          onSubmit={handleSubmit(({ currentPassword, newPassword }) =>
            mutation.mutate({ current_password: currentPassword, new_password: newPassword }),
          )}
        >
          <div className="md:col-span-2">
            <PasswordField
              label={isTurkish ? 'Mevcut sifre' : 'Current password'}
              autoComplete="current-password"
              error={errors.currentPassword?.message}
              {...register('currentPassword')}
            />
          </div>
          <PasswordField
            label={isTurkish ? 'Yeni sifre' : 'New password'}
            autoComplete="new-password"
            error={errors.newPassword?.message}
            {...register('newPassword')}
          />
          <PasswordField
            label={isTurkish ? 'Yeni sifre tekrar' : 'Confirm new password'}
            autoComplete="new-password"
            error={errors.confirmNewPassword?.message}
            {...register('confirmNewPassword')}
          />
          <div className="flex justify-end md:col-span-2">
            <Button type="submit" loading={mutation.isPending} disabled={!isDirty}>
              {isTurkish ? 'Sifreyi guncelle' : 'Update password'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
