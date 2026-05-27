import { ShieldCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { LanguageToggle } from '@/i18n/language-toggle'
import { useLanguage } from '@/i18n/language-provider'
import { ThemeToggle } from '@/theme/theme-toggle'
import { useUserStore } from '@/store/user-store'

type TopBarProps = {
  title: string
  subtitle: string
}

export function TopBar({ title, subtitle }: TopBarProps) {
  const { isTurkish } = useLanguage()
  const profile = useUserStore((s) => s.profile)

  return (
    <header
      className="flex flex-col gap-2 border-b border-[var(--line-soft)] bg-[var(--topbar-surface)] px-3 pb-3 backdrop-blur-xl sm:gap-3 sm:px-5 sm:pb-4 md:px-8 md:pb-5 lg:flex-row lg:items-center lg:justify-between lg:gap-5"
      style={{ paddingTop: 'calc(env(safe-area-inset-top, 0px) + 0.75rem)' }}
    >
      <div className="min-w-0">
        <p className="text-lg font-bold tracking-tight text-[var(--text-strong)] sm:text-xl md:text-2xl">{title}</p>
        <p className="mt-1 hidden text-xs text-[var(--text-muted)] sm:block sm:text-sm">{subtitle}</p>
      </div>

      <div className="flex shrink-0 items-center gap-2 md:gap-3">
        <LanguageToggle />
        <ThemeToggle />
        {/* Badge: icon-only on xs, full text from sm */}
        <Badge variant="success" className="hidden gap-2 px-3 py-1.5 sm:inline-flex">
          <ShieldCheck className="size-4" />
          {isTurkish ? 'Yerel-oncelikli gizlilik' : 'Local-first privacy'}
        </Badge>
        <Badge variant="success" className="gap-1 px-2 py-1.5 sm:hidden">
          <ShieldCheck className="size-3.5" />
        </Badge>
        {profile ? (
          <div className="shrink-0 rounded-xl border border-[var(--line-soft)] bg-[var(--surface)] px-3 py-2 sm:rounded-2xl md:px-4 md:py-3">
            <p className="max-w-[72px] truncate text-xs font-semibold text-[var(--text-strong)] sm:max-w-none sm:text-sm">{profile.display_name}</p>
            <p className="hidden text-xs text-[var(--text-muted)] md:block">{profile.locale}</p>
          </div>
        ) : null}
      </div>
    </header>
  )
}
