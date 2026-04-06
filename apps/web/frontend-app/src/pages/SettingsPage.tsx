import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { authApi } from '@/api/auth'
import { toErrorMessage } from '@/api/client'
import { userApi } from '@/api/user'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { LoadingCard } from '@/components/ui/loading-state'
import { ConsentForm } from '@/features/settings/components/ConsentForm'
import { ProfileForm } from '@/features/settings/components/ProfileForm'
import { SettingsForm } from '@/features/settings/components/SettingsForm'
import { useAuth } from '@/hooks/use-auth'

export function SettingsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { session, clearSession } = useAuth()
  const userContextQuery = useQuery({
    queryKey: ['user-context'],
    queryFn: userApi.getMe,
  })

  const profileMutation = useMutation({
    mutationFn: userApi.updateProfile,
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['user-context'] })
      toast.success('Profile updated.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to update profile.'))
    },
  })

  const settingsMutation = useMutation({
    mutationFn: userApi.updateSettings,
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['user-context'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Monitoring preferences updated.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to update monitoring preferences.'))
    },
  })

  const consentMutation = useMutation({
    mutationFn: userApi.updateConsents,
    onSuccess() {
      void queryClient.invalidateQueries({ queryKey: ['user-context'] })
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success('Consent preferences updated.')
    },
    onError(error) {
      toast.error(toErrorMessage(error, 'Unable to update consent settings.'))
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
      queryClient.clear()
      toast.success('Signed out.')
      navigate('/login', { replace: true })
    },
  })

  if (userContextQuery.isLoading || !userContextQuery.data) {
    return <LoadingCard message="Loading account settings" />
  }

  const user = userContextQuery.data

  return (
    <div className="space-y-6">
      <ProfileForm user={user} isSaving={profileMutation.isPending} onSubmit={(values) => profileMutation.mutate(values)} />
      <SettingsForm
        settings={user.settings}
        isSaving={settingsMutation.isPending}
        onSubmit={(values) => settingsMutation.mutate(values)}
      />
      <ConsentForm
        consents={user.consents}
        modelMode={user.settings.model_mode}
        isSaving={consentMutation.isPending}
        onSubmit={(values) => consentMutation.mutate(values)}
      />

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Session security</CardTitle>
            <CardDescription className="mt-2">Use the auth-service logout endpoint to revoke the current refresh token and clear the local session.</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold text-white">Logout</p>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">This will terminate the persisted frontend session and require a fresh sign-in.</p>
          </div>
          <Button variant="danger" loading={logoutMutation.isPending} onClick={() => logoutMutation.mutate()}>
            Sign out
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

