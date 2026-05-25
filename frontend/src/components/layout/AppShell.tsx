import type { PropsWithChildren } from 'react'
import { useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopBar } from '@/components/layout/TopBar'
import { MobileNav } from '@/components/layout/MobileNav'
import { LoadingScreen } from '@/components/ui/loading-state'
import { useLanguage } from '@/i18n/language-provider'
import { userApi } from '@/api/user'
import { useUserStore } from '@/store/user-store'

const routeMeta: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': {
    title: 'Live Monitoring',
    subtitle: 'Camera-guided behavior analysis, activity feed, and reminder controls.',
  },
  '/history': {
    title: 'History',
    subtitle: 'Weekly trends and detailed event timelines based on monitoring results.',
  },
  '/reports': {
    title: 'Reports',
    subtitle: 'Daily summaries, recommendations, reminder history, and end-of-day context.',
  },
  '/chat': {
    title: 'Grounded Chat',
    subtitle: 'Ask about your own tracked behavior, hydration, reminders, and risky cues.',
  },
  '/settings': {
    title: 'Settings',
    subtitle: 'Profile, sensitivity, reminder cadence, privacy, and session controls.',
  },
}

export function AppShell({ children }: PropsWithChildren) {
  const { isTurkish } = useLanguage()
  const location = useLocation()
  const setProfile = useUserStore((s) => s.setProfile)
  const { data, isLoading } = useQuery({
    queryKey: ['user-context'],
    queryFn: async () => {
      const profile = await userApi.getMe()
      setProfile(profile)
      return profile
    },
  })

  if (isLoading || !data) {
    return <LoadingScreen message={isTurkish ? 'BADHABINOT calisma alani yukleniyor' : 'Loading your BADHABINOT workspace'} />
  }

  const meta =
    routeMeta[location.pathname] ??
    (isTurkish
      ? {
          title: 'BADHABINOT',
          subtitle: 'Davranis zekasi, su destegi ve oturum gorunurlugu.',
        }
      : {
          title: 'BADHABINOT',
          subtitle: 'Behavior intelligence, hydration support, and session visibility.',
        })

  const translatedMeta = isTurkish
    ? {
        '/dashboard': {
          title: 'Canli Izleme',
          subtitle: 'Kamera destekli davranis analizi, aktivite akis ve hatirlatici kontrolleri.',
        },
        '/history': {
          title: 'Gecmis',
          subtitle: 'Izleme sonuclarina dayali haftalik trendler ve ayrintili olay zaman cizelgesi.',
        },
        '/reports': {
          title: 'Raporlar',
          subtitle: 'Gunluk ozetler, oneriler, hatirlatici gecmisi ve gun sonu baglami.',
        },
        '/chat': {
          title: 'Veriye Dayali Sohbet',
          subtitle: 'Kendi davranis verilerin, su takibi, hatirlaticilar ve riskli ipuclari hakkinda sor.',
        },
        '/settings': {
          title: 'Ayarlar',
          subtitle: 'Profil, hassasiyet, hatirlatici araligi, gizlilik ve oturum kontrolleri.',
        },
      }[location.pathname] ?? meta
    : meta

  return (
    <div className="app-shell-grid flex min-h-screen bg-transparent">
      <Sidebar user={data} />
      <div className="flex min-h-screen flex-1 flex-col">
        <TopBar title={translatedMeta.title} subtitle={translatedMeta.subtitle} />
        <main className="flex-1 px-4 py-5 pb-32 md:px-8 md:py-6 lg:pb-8">
          {children}
        </main>
      </div>
      <MobileNav />
    </div>
  )
}
