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
    <header className="flex flex-col gap-5 border-b border-[var(--line-soft)] bg-[var(--topbar-surface)] px-5 py-5 backdrop-blur-xl md:px-8 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <p className="text-2xl font-bold tracking-tight text-[var(--text-strong)]">{title}</p>
        <p className="mt-1 text-sm text-[var(--text-muted)]">{subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        <LanguageToggle />
        <ThemeToggle />
        <Badge variant="success" className="gap-2 px-3 py-1.5">
          <ShieldCheck className="size-4" />
          {isTurkish ? 'Yerel-oncelikli gizlilik' : 'Local-first privacy'}
        </Badge>
        {profile ? (
          <div className="rounded-2xl border border-[var(--line-soft)] bg-[var(--surface)] px-4 py-3">
            <p className="text-sm font-semibold text-[var(--text-strong)]">{profile.display_name}</p>
            <p className="text-xs text-[var(--text-muted)]">{profile.locale}</p>
          </div>
        ) : null}
      </div>
    </header>
  )
}
