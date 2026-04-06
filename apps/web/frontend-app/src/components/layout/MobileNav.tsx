import { History, LayoutDashboard, Settings } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/cn'

const items = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/history', label: 'History', icon: History },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function MobileNav() {
  return (
    <nav className="fixed inset-x-4 bottom-4 z-30 flex items-center justify-between rounded-[28px] border border-[var(--line-soft)] bg-[var(--nav-surface)] px-4 py-3 shadow-[var(--shadow-panel)] backdrop-blur-xl lg:hidden">
      {items.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            cn(
              'flex flex-1 flex-col items-center gap-1 rounded-2xl px-3 py-2 text-[11px] font-semibold text-[var(--text-muted)] transition',
              isActive && 'bg-[var(--primary-soft)] text-[var(--text-on-accent)]',
            )
          }
        >
          <Icon className="size-4" />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
