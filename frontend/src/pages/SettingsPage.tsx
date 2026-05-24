import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { UserRound } from 'lucide-react'
import { authApi } from '@/api/auth'
import { toErrorMessage } from '@/api/client'
import { userApi } from '@/api/user'
import { monitoringApi } from '@/api/monitoring'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { LoadingCard } from '@/components/ui/loading-state'
import { AiModeForm } from '@/features/settings/components/AiModeForm'
import { ConsentForm } from '@/features/settings/components/ConsentForm'
import { PasswordChangeForm } from '@/features/settings/components/PasswordChangeForm'
import { ProfileForm } from '@/features/settings/components/ProfileForm'
import { SettingsForm } from '@/features/settings/components/SettingsForm'
import { FaceRegistrationModal } from '@/features/dashboard/components/FaceRegistrationModal'
import { useAuth } from '@/hooks/use-auth'
import { useLanguage } from '@/i18n/language-provider'
import { useUserStore } from '@/store/user-store'

export function SettingsPage() {
  const { isTurkish } = useLanguage()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { session, clearSession } = useAuth()
  const storeProfile = useUserStore((s) => s.profile)
  const clearUser = useUserStore((s) => s.clearUser)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deletePassword, setDeletePassword] = useState('')
  const [faceRegOpen, setFaceRegOpen] = useState(false)
  const [deleteFaceConfirmOpen, setDeleteFaceConfirmOpen] = useState(false)
  const userContextQuery = useQuery({
    queryKey: ['user-context'],
    queryFn: userApi.getMe,
    initialData: storeProfile ?? undefined,
  })

  const profileMutation = useMutation({
    mutationFn: userApi.updateProfile,
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['user-context'] })
      toast.success(isTurkish ? 'Profil guncellendi.' : 'Profile updated.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Profil guncellenemedi.' : 'Unable to update profile.'))
    },
  })

  const settingsMutation = useMutation({
    mutationFn: userApi.updateSettings,
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['user-context'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isTurkish ? 'Izleme tercihleri guncellendi.' : 'Monitoring preferences updated.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Izleme tercihleri guncellenemedi.' : 'Unable to update monitoring preferences.'))
    },
  })

  const consentMutation = useMutation({
    mutationFn: userApi.updateConsents,
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['user-context'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(isTurkish ? 'Onay tercihleri guncellendi.' : 'Consent preferences updated.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Onay ayarlari guncellenemedi.' : 'Unable to update consent settings.'))
    },
  })

  const deleteAccountMutation = useMutation({
    mutationFn: () => userApi.deleteAccount({ password: deletePassword }),
    onSuccess() {
      clearSession()
      clearUser()
      queryClient.clear()
      toast.success(isTurkish ? 'Hesabınız silindi.' : 'Account deleted.')
      navigate('/login', { replace: true })
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Hesap silinemedi.' : 'Unable to delete account.'))
      setDeleteDialogOpen(false)
    },
  })

  const logoutMutation = useMutation({
    mutationFn: async () => {
      if (session?.refresh_token) {
        await authApi.logout({ refresh_token: session.refresh_token })
      }
    },
    onSettled() {
      clearSession()
      clearUser()
      queryClient.clear()
      toast.success(isTurkish ? 'Cikis yapildi.' : 'Signed out.')
      navigate('/login', { replace: true })
    },
  })

  const faceStatusQuery = useQuery({
    queryKey: ['face-status'],
    queryFn: monitoringApi.faceStatus,
    staleTime: 30_000,
  })

  const deleteFaceMutation = useMutation({
    mutationFn: monitoringApi.deleteFaceProfile,
    onSuccess() {
      void faceStatusQuery.refetch()
      void queryClient.invalidateQueries({ queryKey: ['face-status'] })
      toast.success(isTurkish ? 'Yüz profili silindi.' : 'Face profile deleted.')
      setDeleteFaceConfirmOpen(false)
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Yüz profili silinemedi.' : 'Unable to delete face profile.'))
      setDeleteFaceConfirmOpen(false)
    },
  })

  if (userContextQuery.isLoading || !userContextQuery.data) {
    return <LoadingCard message={isTurkish ? 'Hesap ayarlari yukleniyor' : 'Loading account settings'} />
  }

  const user = userContextQuery.data
  const faceRegistered = faceStatusQuery.data?.success ?? false

  return (
    <div className="space-y-6">
      <ProfileForm user={user} isSaving={profileMutation.isPending} onSubmit={(values) => profileMutation.mutate(values)} />
      <PasswordChangeForm />
      <SettingsForm
        settings={user.settings}
        isSaving={settingsMutation.isPending}
        onSubmit={(values) =>
          settingsMutation.mutate({
            ...values,
            model_mode: user.settings.model_mode,
            local_model_name: user.settings.local_model_name,
            ollama_base_url: user.settings.ollama_base_url,
          })
        }
      />
      <AiModeForm
        settings={user.settings}
        isSaving={settingsMutation.isPending}
        onSubmit={(aiValues) =>
          settingsMutation.mutate({
            sensitivity: user.settings.sensitivity,
            water_goal_ml: user.settings.water_goal_ml,
            water_interval_min: user.settings.water_interval_min,
            exercise_interval_min: user.settings.exercise_interval_min,
            quiet_hours_enabled: user.settings.quiet_hours_enabled,
            quiet_hours_start: user.settings.quiet_hours_start,
            quiet_hours_end: user.settings.quiet_hours_end,
            notifications_enabled: user.settings.notifications_enabled,
            ...aiValues,
          })
        }
      />
      <ConsentForm
        consents={user.consents}
        isSaving={consentMutation.isPending}
        onSubmit={(values) => consentMutation.mutate(values)}
      />

      {/* Face recognition management */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>{isTurkish ? 'Yüz Tanıma' : 'Face Recognition'}</CardTitle>
            <CardDescription className="mt-2">
              {isTurkish
                ? 'Yüz tanıma ile giriş yapmak ve davranış analizini etkinleştirmek için yüzünüzü kaydedin.'
                : 'Register your face to enable face login and behavior analysis features.'}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <div className={`flex size-10 items-center justify-center rounded-2xl ${faceRegistered ? 'bg-[var(--success)]/10' : 'bg-[var(--surface-muted)]'}`}>
              <UserRound className={`size-5 ${faceRegistered ? 'text-[var(--success)]' : 'text-[var(--text-muted)]'}`} />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">
                {faceRegistered
                  ? isTurkish ? 'Yüz kaydı aktif ✓' : 'Face registered ✓'
                  : isTurkish ? 'Yüz kaydı yok' : 'No face registered'}
              </p>
              <p className="text-sm text-[var(--text-muted)]">
                {faceRegistered
                  ? (isTurkish
                    ? `${faceStatusQuery.data?.frames_enrolled ?? 0} kare kaydedildi`
                    : `${faceStatusQuery.data?.frames_enrolled ?? 0} frames enrolled`)
                  : (isTurkish
                    ? 'Yüz tanıma devre dışı'
                    : 'Face recognition disabled')}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button
              variant="secondary"
              onClick={() => setFaceRegOpen(true)}
            >
              {faceRegistered
                ? isTurkish ? 'Yüzü Güncelle' : 'Update Face'
                : isTurkish ? 'Yüz Kaydı Yap' : 'Register Face'}
            </Button>
            {faceRegistered && (
              <Button
                variant="danger"
                onClick={() => setDeleteFaceConfirmOpen(true)}
              >
                {isTurkish ? 'Yüz Kaydını Sil' : 'Delete Face Profile'}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="border-[var(--danger)]/30">
        <CardHeader>
          <div>
            <CardTitle className="text-[var(--danger)]">{isTurkish ? 'Hesabı Sil' : 'Delete account'}</CardTitle>
            <CardDescription className="mt-2">
              {isTurkish
                ? 'Bu işlem geri alınamaz. Tüm verileriniz kalıcı olarak silinir.'
                : 'This action is irreversible. All your data will be permanently deleted.'}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <p className="text-sm leading-6 text-[var(--text-muted)]">
            {isTurkish
              ? 'İzleme geçmişiniz, raporlarınız, ayarlarınız ve kimlik bilgileriniz silinir.'
              : 'Your monitoring history, reports, settings, and credentials will be erased.'}
          </p>
          <Button variant="danger" onClick={() => { setDeletePassword(''); setDeleteDialogOpen(true) }}>
            {isTurkish ? 'Hesabı sil' : 'Delete account'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>{isTurkish ? 'Oturum guvenligi' : 'Session security'}</CardTitle>
            <CardDescription className="mt-2">
              {isTurkish
                ? 'Mevcut yenileme belirtecini iptal edip yerel oturumu temizlemek icin auth-service cikis uc noktasini kullan.'
                : 'Use the auth-service logout endpoint to revoke the current refresh token and clear the local session.'}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold text-white">{isTurkish ? 'Cikis' : 'Logout'}</p>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
              {isTurkish
                ? 'Bu islem kalici on yuz oturumunu sonlandirir ve yeniden giris ister.'
                : 'This will terminate the persisted frontend session and require a fresh sign-in.'}
            </p>
          </div>
          <Button variant="danger" loading={logoutMutation.isPending} onClick={() => logoutMutation.mutate()}>
            {isTurkish ? 'Cikis yap' : 'Sign out'}
          </Button>
        </CardContent>
      </Card>

      <ConfirmDialog
        isOpen={deleteDialogOpen}
        variant="danger"
        title={isTurkish ? 'Hesabı kalıcı olarak sil' : 'Permanently delete account'}
        confirmLabel={isTurkish ? 'Hesabı sil' : 'Delete account'}
        cancelLabel={isTurkish ? 'Vazgeç' : 'Cancel'}
        loading={deleteAccountMutation.isPending}
        onCancel={() => setDeleteDialogOpen(false)}
        onConfirm={() => deleteAccountMutation.mutate()}
        description={
          <div className="flex flex-col gap-3">
            <p>
              {isTurkish
                ? 'Bu işlem geri alınamaz. Devam etmek için şifrenizi girin.'
                : 'This cannot be undone. Enter your password to continue.'}
            </p>
            <input
              type="password"
              autoComplete="current-password"
              placeholder={isTurkish ? 'Şifreniz' : 'Your password'}
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              className="h-11 w-full rounded-2xl border border-[var(--line-soft)] bg-[var(--surface-subtle)] px-4 text-sm text-[var(--text-strong)] outline-none transition placeholder:text-[var(--text-soft)] focus:border-[var(--danger)] focus:bg-[var(--surface-soft)]"
            />
          </div>
        }
      />

      {faceRegOpen && (
        <FaceRegistrationModal
          onClose={() => {
            setFaceRegOpen(false)
            void faceStatusQuery.refetch()
          }}
        />
      )}

      <ConfirmDialog
        isOpen={deleteFaceConfirmOpen}
        variant="danger"
        title={isTurkish ? 'Yüz profilini sil' : 'Delete face profile'}
        description={
          isTurkish
            ? 'Bu işlem kayıtlı yüz verinizi kalıcı olarak siler. Yüz tanıma ve yüz ile giriş devre dışı kalır.'
            : 'This permanently deletes your enrolled face data. Face recognition and face login will be disabled.'
        }
        confirmLabel={isTurkish ? 'Sil' : 'Delete'}
        cancelLabel={isTurkish ? 'Vazgeç' : 'Cancel'}
        loading={deleteFaceMutation.isPending}
        onConfirm={() => deleteFaceMutation.mutate()}
        onCancel={() => setDeleteFaceConfirmOpen(false)}
      />
    </div>
  )
}
