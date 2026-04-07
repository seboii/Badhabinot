import type { PropsWithChildren } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopBar } from '@/components/layout/TopBar'
import { MobileNav } from '@/components/layout/MobileNav'
import { LoadingScreen } from '@/components/ui/loading-state'
import { userApi } from '@/api/user'

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
  const location = useLocation()
  const { data, isLoading } = useQuery({
    queryKey: ['user-context'],
    queryFn: userApi.getMe,
  })

  if (isLoading || !data) {
    return <LoadingScreen message="Loading your BADHABINOT workspace" />
  }

  const needsOnboarding =
    !data.consents.privacy_policy_accepted || !data.consents.camera_monitoring_accepted

  if (needsOnboarding) {
    return <Navigate replace to="/onboarding" />
  }

  const meta = routeMeta[location.pathname] ?? {
    title: 'BADHABINOT',
    subtitle: 'Behavior intelligence, hydration support, and session visibility.',
  }

  return (
    <div className="app-shell-grid flex min-h-screen bg-transparent">
      <Sidebar user={data} />
      <div className="flex min-h-screen flex-1 flex-col">
        <TopBar title={meta.title} subtitle={meta.subtitle} user={data} />
        <main className="flex-1 px-5 py-6 pb-28 md:px-8 lg:pb-8">{children}</main>
      </div>
      <MobileNav />
    </div>
  )
}
