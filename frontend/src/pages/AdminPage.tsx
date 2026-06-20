import { useMemo, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  Activity,
  FileText,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
  UserRound,
  Users,
} from 'lucide-react'
import { adminApi } from '@/api/admin'
import { toErrorMessage } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
import { LoadingCard } from '@/components/ui/loading-state'
import { useAuth } from '@/hooks/use-auth'
import { useLanguage } from '@/i18n/language-provider'
import { formatDateTime, formatRelativeTime } from '@/lib/format'

function StatCard({ label, value, icon: Icon }: { label: string; value: number | string; icon: typeof Users }) {
  return (
    <Card>
      <CardContent className="p-3 sm:p-4">
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-[var(--text-muted)]">{label}</p>
            <p className="mt-1 text-xl font-extrabold text-white sm:text-2xl">{value}</p>
          </div>
          <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[var(--primary-soft)]">
            <Icon className="size-4 text-[var(--primary)]" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-[var(--line-soft)] py-2 last:border-0">
      <span className="text-sm text-[var(--text-muted)]">{label}</span>
      <span className="text-right text-sm font-semibold text-white">{value}</span>
    </div>
  )
}

export function AdminPage() {
  const { isTurkish, language } = useLanguage()
  const { isAdmin, session } = useAuth()
  const queryClient = useQueryClient()

  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [resetOpen, setResetOpen] = useState(false)

  const statsQuery = useQuery({ queryKey: ['admin-stats'], queryFn: adminApi.getStats })
  const usersQuery = useQuery({
    queryKey: ['admin-users', search],
    queryFn: () => adminApi.listUsers({ search, size: 50 }),
  })
  const detailQuery = useQuery({
    queryKey: ['admin-user', selectedId],
    queryFn: () => adminApi.getUser(selectedId as string),
    enabled: Boolean(selectedId),
  })
  const reportsQuery = useQuery({
    queryKey: ['admin-user-reports', selectedId],
    queryFn: () => adminApi.getUserReports(selectedId as string, 30),
    enabled: Boolean(selectedId),
  })

  const deleteMutation = useMutation({
    mutationFn: () => adminApi.deleteUser(selectedId as string),
    onSuccess() {
      toast.success(isTurkish ? 'Hesap silindi.' : 'Account deleted.')
      setDeleteOpen(false)
      setSelectedId(null)
      void queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      void queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Hesap silinemedi.' : 'Unable to delete account.'))
      setDeleteOpen(false)
    },
  })

  const resetMutation = useMutation({
    mutationFn: () => adminApi.resetUserData(selectedId as string),
    onSuccess() {
      toast.success(isTurkish ? 'Kullanıcı verileri sıfırlandı.' : 'User data reset.')
      setResetOpen(false)
      void queryClient.invalidateQueries({ queryKey: ['admin-user', selectedId] })
      void queryClient.invalidateQueries({ queryKey: ['admin-user-reports', selectedId] })
      void queryClient.invalidateQueries({ queryKey: ['admin-stats'] })
    },
    onError(error) {
      toast.error(toErrorMessage(error, isTurkish ? 'Veriler sıfırlanamadı.' : 'Unable to reset data.'))
      setResetOpen(false)
    },
  })

  const users = usersQuery.data?.items ?? []
  const detail = detailQuery.data
  const reports = reportsQuery.data ?? []
  const stats = statsQuery.data

  const selfId = session?.user.id
  const isSelfSelected = useMemo(() => Boolean(selectedId && selectedId === selfId), [selectedId, selfId])

  // Sadece admin görebilir — değilse panele yönlendir.
  if (!isAdmin) {
    return <Navigate replace to="/dashboard" />
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-extrabold tracking-tight text-white">
          <ShieldCheck className="size-6 text-[var(--primary)]" />
          {isTurkish ? 'Yönetim Paneli' : 'Admin Panel'}
        </h1>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          {isTurkish
            ? 'Tüm kullanıcıları görüntüle, raporlarına eriş, hesapları yönet.'
            : 'View all users, access their reports, and manage accounts.'}
        </p>
      </div>

      {/* ── İstatistikler ─────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard label={isTurkish ? 'Kullanıcı' : 'Users'} value={stats?.total_users ?? '—'} icon={Users} />
        <StatCard label={isTurkish ? 'Admin' : 'Admins'} value={stats?.admin_count ?? '—'} icon={ShieldCheck} />
        <StatCard label={isTurkish ? 'Oturum' : 'Sessions'} value={stats?.total_sessions ?? '—'} icon={Activity} />
        <StatCard label={isTurkish ? 'Analiz' : 'Analyses'} value={stats?.total_analyses ?? '—'} icon={Activity} />
        <StatCard label={isTurkish ? 'Rapor' : 'Reports'} value={stats?.total_reports ?? '—'} icon={FileText} />
        <StatCard label={isTurkish ? 'Olay' : 'Events'} value={stats?.total_events ?? '—'} icon={Activity} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.5fr)]">
        {/* ── Kullanıcı listesi ──────────────────────────────────── */}
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>{isTurkish ? 'Kullanıcılar' : 'Users'}</CardTitle>
            <CardDescription className="mt-1">
              {usersQuery.data ? `${usersQuery.data.total} ${isTurkish ? 'kayıt' : 'total'}` : '—'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--text-soft)]" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={isTurkish ? 'E-posta ara…' : 'Search email…'}
                className="h-11 w-full rounded-2xl border border-[var(--line-soft)] bg-[var(--surface-subtle)] pl-10 pr-4 text-sm text-[var(--text-strong)] outline-none transition placeholder:text-[var(--text-soft)] focus:border-[var(--primary)]"
              />
            </div>

            {usersQuery.isLoading ? (
              <LoadingCard message={isTurkish ? 'Kullanıcılar yükleniyor' : 'Loading users'} />
            ) : users.length === 0 ? (
              <p className="py-6 text-center text-sm text-[var(--text-muted)]">
                {isTurkish ? 'Kullanıcı bulunamadı.' : 'No users found.'}
              </p>
            ) : (
              <div className="max-h-[60vh] space-y-2 overflow-y-auto pr-1">
                {users.map((u) => (
                  <button
                    key={u.id}
                    type="button"
                    onClick={() => setSelectedId(u.id)}
                    className={`flex w-full items-center gap-3 rounded-2xl border p-3 text-left transition ${
                      selectedId === u.id
                        ? 'border-[var(--primary)] bg-[var(--primary-soft)]'
                        : 'border-[var(--line-soft)] bg-[rgba(255,255,255,0.02)] hover:bg-[var(--surface-hover)]'
                    }`}
                  >
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[var(--surface-muted)]">
                      <UserRound className="size-4 text-[var(--text-muted)]" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-white">{u.display_name || u.email}</p>
                      <p className="truncate text-xs text-[var(--text-muted)]">{u.email}</p>
                    </div>
                    {u.role === 'ADMIN' ? <Badge variant="primary">admin</Badge> : null}
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* ── Seçili kullanıcı detayı ────────────────────────────── */}
        {!selectedId ? (
          <Card className="flex min-h-[300px] items-center justify-center">
            <CardContent className="p-8 text-center">
              <UserRound className="mx-auto size-10 text-[var(--text-soft)]" />
              <p className="mt-3 text-sm text-[var(--text-muted)]">
                {isTurkish ? 'Detay için bir kullanıcı seç.' : 'Select a user to see details.'}
              </p>
            </CardContent>
          </Card>
        ) : detailQuery.isLoading || !detail ? (
          <LoadingCard message={isTurkish ? 'Kullanıcı yükleniyor' : 'Loading user'} />
        ) : (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0">
                    <CardTitle className="truncate">{detail.profile?.display_name || detail.email}</CardTitle>
                    <CardDescription className="mt-1 truncate">{detail.email}</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={detail.role === 'ADMIN' ? 'primary' : 'neutral'}>{detail.role}</Badge>
                    <Badge variant={detail.status === 'ACTIVE' ? 'success' : 'warning'}>{detail.status}</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <p className="mb-1 text-xs uppercase tracking-[0.14em] text-[var(--text-soft)]">{isTurkish ? 'Hesap' : 'Account'}</p>
                    <InfoRow label={isTurkish ? 'Kayıt' : 'Created'} value={formatDateTime(detail.created_at, language)} />
                    <InfoRow label={isTurkish ? 'Son giriş' : 'Last login'} value={detail.last_login_at ? formatRelativeTime(detail.last_login_at, language) : '—'} />
                    <InfoRow label={isTurkish ? 'Saat dilimi' : 'Timezone'} value={detail.profile?.timezone ?? '—'} />
                    <InfoRow label={isTurkish ? 'Yüz kaydı' : 'Face'} value={detail.face.enrolled ? `${detail.face.frames_enrolled} ${isTurkish ? 'kare' : 'frames'}` : (isTurkish ? 'Yok' : 'None')} />
                  </div>
                  <div>
                    <p className="mb-1 text-xs uppercase tracking-[0.14em] text-[var(--text-soft)]">{isTurkish ? 'Ayarlar' : 'Settings'}</p>
                    <InfoRow label={isTurkish ? 'Hassasiyet' : 'Sensitivity'} value={detail.settings?.sensitivity ?? '—'} />
                    <InfoRow label={isTurkish ? 'Model modu' : 'Model mode'} value={detail.settings?.model_mode ?? '—'} />
                    <InfoRow label={isTurkish ? 'Su hedefi' : 'Water goal'} value={detail.settings ? `${detail.settings.water_goal_ml} ml` : '—'} />
                    <InfoRow label={isTurkish ? 'Bildirimler' : 'Notifications'} value={detail.settings?.notifications_enabled ? (isTurkish ? 'Açık' : 'On') : (isTurkish ? 'Kapalı' : 'Off')} />
                  </div>
                </div>

                {/* Veri istatistikleri */}
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                  {([
                    [isTurkish ? 'Oturum' : 'Sessions', detail.stats.sessions],
                    [isTurkish ? 'Analiz' : 'Analyses', detail.stats.analyses],
                    [isTurkish ? 'Olay' : 'Events', detail.stats.events],
                    [isTurkish ? 'Rapor' : 'Reports', detail.stats.reports],
                    [isTurkish ? 'Sohbet' : 'Chat', detail.stats.chat_messages],
                  ] as const).map(([label, value]) => (
                    <div key={label} className="rounded-2xl border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-3 text-center">
                      <p className="text-lg font-bold text-white">{value}</p>
                      <p className="text-xs text-[var(--text-muted)]">{label}</p>
                    </div>
                  ))}
                </div>

                {/* İşlemler */}
                <div className="flex flex-wrap gap-3 border-t border-[var(--line-soft)] pt-4">
                  <Button variant="secondary" iconLeft={<RefreshCw className="size-4" />} onClick={() => setResetOpen(true)}>
                    {isTurkish ? 'Verileri sıfırla' : 'Reset data'}
                  </Button>
                  <Button variant="danger" iconLeft={<Trash2 className="size-4" />} onClick={() => setDeleteOpen(true)}>
                    {isTurkish ? 'Hesabı sil' : 'Delete account'}
                  </Button>
                  {isSelfSelected ? (
                    <span className="self-center text-xs text-[var(--warning)]">
                      {isTurkish ? '⚠ Bu senin hesabın' : '⚠ This is your account'}
                    </span>
                  ) : null}
                </div>
              </CardContent>
            </Card>

            {/* Raporlar */}
            <Card>
              <CardHeader>
                <CardTitle>{isTurkish ? 'Günlük Raporlar' : 'Daily Reports'}</CardTitle>
                <CardDescription className="mt-1">
                  {isTurkish ? 'Kullanıcının en son günlük raporları.' : "The user's most recent daily reports."}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {reportsQuery.isLoading ? (
                  <LoadingCard />
                ) : reports.length === 0 ? (
                  <p className="py-4 text-center text-sm text-[var(--text-muted)]">
                    {isTurkish ? 'Henüz rapor yok.' : 'No reports yet.'}
                  </p>
                ) : (
                  <div className="space-y-3">
                    {reports.map((r) => (
                      <div key={r.report_date} className="rounded-2xl border border-[var(--line-soft)] bg-[rgba(255,255,255,0.03)] p-4">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <p className="text-sm font-semibold text-white">{formatDateTime(r.report_date, language)}</p>
                          <div className="flex flex-wrap gap-1.5">
                            <Badge variant="info">{r.analyses_completed} {isTurkish ? 'analiz' : 'analyses'}</Badge>
                            <Badge variant="warning">{r.posture_alert_count} {isTurkish ? 'duruş' : 'posture'}</Badge>
                            {r.smoking_like_count > 0 ? <Badge variant="danger">{r.smoking_like_count} 🚬</Badge> : null}
                          </div>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--text-muted)]">
                          <span>{isTurkish ? 'El hareketi' : 'Hand'}: {r.hand_movement_count}</span>
                          <span>{isTurkish ? 'Hatırlatıcı' : 'Reminders'}: {r.reminder_count}</span>
                          <span>{isTurkish ? 'Su' : 'Water'}: {r.hydration_progress_ml}/{r.water_goal_ml} ml</span>
                          <span>{isTurkish ? 'Kötü duruş oranı' : 'Poor posture'}: {Math.round(r.poor_posture_ratio * 100)}%</span>
                        </div>
                        {r.summary ? <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{r.summary}</p> : null}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={deleteOpen}
        variant="danger"
        title={isTurkish ? 'Hesabı kalıcı olarak sil' : 'Permanently delete account'}
        description={
          isTurkish
            ? `${detail?.email ?? ''} hesabı ve tüm verileri (izleme, raporlar, ayarlar, yüz profili) kalıcı olarak silinecek. Bu işlem geri alınamaz.`
            : `${detail?.email ?? ''} and all of their data (monitoring, reports, settings, face profile) will be permanently deleted. This cannot be undone.`
        }
        confirmLabel={isTurkish ? 'Hesabı sil' : 'Delete account'}
        cancelLabel={isTurkish ? 'Vazgeç' : 'Cancel'}
        loading={deleteMutation.isPending}
        onConfirm={() => deleteMutation.mutate()}
        onCancel={() => setDeleteOpen(false)}
      />

      <ConfirmDialog
        isOpen={resetOpen}
        variant="danger"
        title={isTurkish ? 'Kullanıcı verilerini sıfırla' : 'Reset user data'}
        description={
          isTurkish
            ? `${detail?.email ?? ''} için tüm izleme oturumları, analizler, olaylar, raporlar, sohbet ve yüz profili silinecek. Hesap ve ayarlar korunur.`
            : `All monitoring sessions, analyses, events, reports, chat, and face profile for ${detail?.email ?? ''} will be deleted. The account and settings are kept.`
        }
        confirmLabel={isTurkish ? 'Sıfırla' : 'Reset'}
        cancelLabel={isTurkish ? 'Vazgeç' : 'Cancel'}
        loading={resetMutation.isPending}
        onConfirm={() => resetMutation.mutate()}
        onCancel={() => setResetOpen(false)}
      />
    </div>
  )
}
