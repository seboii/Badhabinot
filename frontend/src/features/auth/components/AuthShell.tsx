import type { PropsWithChildren } from 'react'
import { Activity, ShieldCheck, Waves } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { LanguageToggle } from '@/i18n/language-toggle'
import { useLanguage } from '@/i18n/language-provider'
import { ThemeToggle } from '@/theme/theme-toggle'

export function AuthShell({
  title,
  subtitle,
  children,
}: PropsWithChildren<{ title: string; subtitle: string }>) {
  const { isTurkish } = useLanguage()

  return (
    <div className="min-h-screen bg-transparent">
      {/* Mobile-only compact header */}
      <div className="flex items-center justify-between border-b border-[var(--line-soft)] px-5 py-4 lg:hidden">
        <p className="text-lg font-extrabold tracking-[-0.03em] text-[var(--text-strong)]">BADHABINOT</p>
        <div className="flex items-center gap-2">
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>

      <div className="px-4 py-5 sm:px-6 md:px-8 md:py-8">
        <div className="mx-auto grid max-w-7xl gap-6 md:gap-8 lg:min-h-[calc(100vh-6rem)] lg:grid-cols-[1.1fr_0.9fr]">

          {/* Hero section — hidden on mobile, visible on desktop */}
          <section className="hidden lg:relative lg:block lg:overflow-hidden lg:rounded-[36px] lg:border lg:border-[var(--line-soft)] lg:bg-[var(--hero-surface)] lg:p-10 lg:shadow-[var(--shadow-panel)]">
            <div className="absolute left-0 top-0 h-72 w-72 rounded-full bg-[var(--primary-glow)] blur-3xl" />
            <div className="relative z-10 flex h-full flex-col justify-between gap-8">
              <div>
                <div className="flex items-center justify-between gap-4">
                  <Badge variant="primary" className="mb-4 gap-2 px-3 py-1.5">
                    <ShieldCheck className="size-4" />
                    {isTurkish ? 'Gizlilik-oncelikli izleme' : 'Privacy-first monitoring'}
                  </Badge>
                  <div className="flex items-center gap-2">
                    <LanguageToggle />
                    <ThemeToggle />
                  </div>
                </div>
                <h1 className="max-w-xl text-5xl font-extrabold tracking-[-0.05em] text-[var(--text-strong)] xl:text-6xl">
                  BADHABINOT
                </h1>
                <p className="mt-4 max-w-xl text-base leading-7 text-[var(--text-muted)] xl:text-lg">
                  {isTurkish
                    ? 'Davranis farkindaligi, durus geri bildirimi, su hatirlaticilari ve aktivite gorunurlugu tek bir yerel-oncelikli yuzde.'
                    : 'Behavior awareness, posture feedback, hydration nudges, and activity visibility in one local-first control surface.'}
                </p>
              </div>

              <div className="grid gap-4 xl:grid-cols-3">
                <div className="rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-soft)] p-5">
                  <Activity className="size-6 text-[var(--primary)]" />
                  <p className="mt-5 text-lg font-bold text-[var(--text-strong)]">{isTurkish ? 'Canli tespit' : 'Live detection'}</p>
                  <p className="mt-2 text-sm text-[var(--text-muted)]">
                    {isTurkish
                      ? 'Web kameran ile durus ve riskli aliskanliklari analiz et.'
                      : 'Use your webcam to analyze posture and risky habits.'}
                  </p>
                </div>
                <div className="rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-soft)] p-5">
                  <Waves className="size-6 text-[var(--info)]" />
                  <p className="mt-5 text-lg font-bold text-[var(--text-strong)]">{isTurkish ? 'Su takibi' : 'Hydration flow'}</p>
                  <p className="mt-2 text-sm text-[var(--text-muted)]">
                    {isTurkish
                      ? 'Su tuketimi, hatirlaticilar ve gunluk serileri takip et.'
                      : 'Track water intake, reminders, and daily streaks.'}
                  </p>
                </div>
                <div className="rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface-soft)] p-5">
                  <ShieldCheck className="size-6 text-[var(--success)]" />
                  <p className="mt-5 text-lg font-bold text-[var(--text-strong)]">{isTurkish ? 'Yerel mod' : 'Local mode'}</p>
                  <p className="mt-2 text-sm text-[var(--text-muted)]">
                    {isTurkish
                      ? 'Varsayilan akislar kareleri cihazda tutar ve ham gorsel saklamaz.'
                      : 'Default workflows keep frames on-device and avoid raw image storage.'}
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Form section — always visible, full width on mobile */}
          <section className="flex items-start justify-center lg:items-center">
            <div className="w-full max-w-xl rounded-[28px] border border-[var(--line-soft)] bg-[var(--hero-panel)] p-6 shadow-[var(--shadow-panel)] sm:rounded-[32px] sm:p-8 lg:p-10">
              <div className="mb-6 sm:mb-8">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--text-soft)] sm:text-sm">
                  {isTurkish ? 'Guvenli erisim' : 'Secure access'}
                </p>
                <h2 className="mt-3 text-2xl font-bold tracking-tight text-[var(--text-strong)] sm:mt-4 sm:text-3xl">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-[var(--text-muted)] sm:mt-3">{subtitle}</p>
              </div>
              {children}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
