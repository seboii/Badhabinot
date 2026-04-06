import type { PropsWithChildren } from 'react'
import { Activity, ShieldCheck, Waves } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { ThemeToggle } from '@/theme/theme-toggle'

export function AuthShell({
  title,
  subtitle,
  children,
}: PropsWithChildren<{ title: string; subtitle: string }>) {
  return (
    <div className="min-h-screen bg-transparent px-5 py-8 md:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="relative overflow-hidden rounded-[36px] border border-[var(--line-soft)] bg-[var(--hero-surface)] p-8 shadow-[var(--shadow-panel)] md:p-10">
          <div className="absolute left-0 top-0 h-72 w-72 rounded-full bg-[var(--primary-glow)] blur-3xl" />
          <div className="relative z-10 flex h-full flex-col justify-between gap-8">
            <div>
              <div className="flex items-center justify-between gap-4">
                <Badge variant="primary" className="mb-4 gap-2 px-3 py-1.5">
                  <ShieldCheck className="size-4" />
                  Privacy-first monitoring
                </Badge>
                <ThemeToggle />
              </div>
              <h1 className="max-w-xl text-4xl font-extrabold tracking-[-0.05em] text-[var(--text-strong)] md:text-6xl">
                BADHABINOT
              </h1>
              <p className="mt-4 max-w-xl text-base leading-7 text-[var(--text-muted)] md:text-lg">
                Behavior awareness, posture feedback, hydration nudges, and activity visibility in one local-first
                control surface.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-soft)] p-5">
                <Activity className="size-6 text-[var(--primary)]" />
                <p className="mt-5 text-lg font-bold text-[var(--text-strong)]">Live detection</p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">Use your webcam to analyze posture and risky habits.</p>
              </div>
              <div className="rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-soft)] p-5">
                <Waves className="size-6 text-[var(--info)]" />
                <p className="mt-5 text-lg font-bold text-[var(--text-strong)]">Hydration flow</p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">Track water intake, reminders, and daily streaks.</p>
              </div>
              <div className="rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-soft)] p-5">
                <ShieldCheck className="size-6 text-[var(--success)]" />
                <p className="mt-5 text-lg font-bold text-[var(--text-strong)]">Local mode</p>
                <p className="mt-2 text-sm text-[var(--text-muted)]">Default workflows keep frames on-device and avoid raw image storage.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="flex items-center justify-center">
          <div className="w-full max-w-xl rounded-[32px] border border-[var(--line-soft)] bg-[var(--hero-panel)] p-8 shadow-[var(--shadow-panel)] md:p-10">
            <div className="mb-8">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--text-soft)]">Secure access</p>
              <h2 className="mt-4 text-3xl font-bold tracking-tight text-[var(--text-strong)]">{title}</h2>
              <p className="mt-3 text-sm leading-6 text-[var(--text-muted)]">{subtitle}</p>
            </div>
            {children}
          </div>
        </section>
      </div>
    </div>
  )
}
