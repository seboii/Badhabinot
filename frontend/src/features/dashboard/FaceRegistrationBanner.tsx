import { useState } from 'react'
import { AlertTriangle, X, UserRound } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { FaceRegistrationModal } from '@/features/dashboard/components/FaceRegistrationModal'
import { monitoringApi } from '@/api/monitoring'
import { useLanguage } from '@/i18n/language-provider'

export function FaceRegistrationBanner() {
  const { isTurkish } = useLanguage()
  const [dismissed, setDismissed] = useState(false)
  const [regOpen, setRegOpen] = useState(false)

  const { data: faceStatus, refetch } = useQuery({
    queryKey: ['face-status'],
    queryFn: monitoringApi.faceStatus,
    staleTime: 60_000,
  })

  // If face is registered OR user dismissed → hide banner
  if (dismissed || faceStatus?.success) return null

  return (
    <>
      <div className="mb-4 flex items-center gap-4 rounded-[20px] border border-[var(--warning)]/40 bg-[rgba(234,179,8,0.08)] px-5 py-4">
        <AlertTriangle className="size-5 shrink-0 text-[var(--warning)]" />
        <p className="flex-1 text-sm text-[var(--text-muted)]">
          {isTurkish
            ? 'Yüz kaydı yapılmadığı için davranış analizi devre dışı. Tam özellikler için yüzünüzü kaydedin.'
            : 'Behavior analysis is disabled — no face registered. Register your face to enable full features.'}
        </p>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="secondary"
            iconLeft={<UserRound className="size-4" />}
            onClick={() => setRegOpen(true)}
          >
            {isTurkish ? 'Yüz Kaydı Yap' : 'Register Face'}
          </Button>
          <button
            type="button"
            className="flex size-7 items-center justify-center rounded-full text-[var(--text-muted)] transition hover:text-white"
            onClick={() => setDismissed(true)}
            aria-label={isTurkish ? 'Kapat' : 'Dismiss'}
          >
            <X className="size-4" />
          </button>
        </div>
      </div>

      {regOpen && (
        <FaceRegistrationModal
          onClose={() => {
            setRegOpen(false)
            void refetch()
          }}
        />
      )}
    </>
  )
}
