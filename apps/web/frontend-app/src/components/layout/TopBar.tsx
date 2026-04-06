import { ShieldCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { ThemeToggle } from '@/theme/theme-toggle'
import type { UserContextResponse } from '@/types/user'

type TopBarProps = {
  title: string
  subtitle: string
  user: UserContextResponse
}

export function TopBar({ title, subtitle, user }: TopBarProps) {
  return (
    <header className="flex flex-col gap-5 border-b border-[var(--line-soft)] bg-[var(--topbar-surface)] px-5 py-5 backdrop-blur-xl md:px-8 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <p className="text-2xl font-bold tracking-tight text-[var(--text-strong)]">{title}</p>
        <p className="mt-1 text-sm text-[var(--text-muted)]">{subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        <ThemeToggle />
        <Badge variant="success" className="gap-2 px-3 py-1.5">
          <ShieldCheck className="size-4" />
          Local-first privacy
        </Badge>
        <div className="rounded-2xl border border-[var(--line-soft)] bg-[var(--surface)] px-4 py-3">
          <p className="text-sm font-semibold text-[var(--text-strong)]">{user.display_name}</p>
          <p className="text-xs text-[var(--text-muted)]">{user.locale}</p>
        </div>
      </div>
    </header>
  )
}
