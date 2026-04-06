import { History, LayoutDashboard, Settings } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/cn'
import type { UserContextResponse } from '@/types/user'

const navigationItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/history', label: 'History', icon: History },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar({ user }: { user: UserContextResponse }) {
  return (
    <aside className="hidden w-[272px] shrink-0 border-r border-[var(--line-soft)] bg-[var(--nav-surface)] px-6 py-7 lg:flex lg:flex-col">
      <div className="mb-10">
        <p className="text-2xl font-extrabold tracking-[-0.04em] text-[var(--text-strong)]">BADHABINOT</p>
        <p className="mt-2 text-sm text-[var(--text-muted)]">Privacy-first monitoring</p>
      </div>

      <nav className="flex flex-1 flex-col gap-2">
        {navigationItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold text-[var(--text-muted)] transition hover:bg-[var(--surface-hover)] hover:text-[var(--text-strong)]',
                isActive && 'bg-[var(--primary)] text-[var(--text-on-accent)] shadow-[var(--shadow-accent)]',
              )
            }
          >
            <Icon className="size-5" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface)] p-4">
        <p className="text-sm font-semibold text-[var(--text-strong)]">{user.display_name}</p>
        <p className="mt-1 truncate text-sm text-[var(--text-muted)]">{user.email}</p>
        <p className="mt-3 text-xs uppercase tracking-[0.18em] text-[var(--text-soft)]">{user.timezone}</p>
      </div>
    </aside>
  )
}
