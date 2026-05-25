import { History, LayoutDashboard, MessageSquare, ScrollText, Settings } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/cn'
import { useLanguage } from '@/i18n/language-provider'

export function MobileNav() {
  const { isTurkish } = useLanguage()
  const items = [
    { to: '/dashboard', label: isTurkish ? 'Panel' : 'Dashboard', icon: LayoutDashboard },
    { to: '/history', label: isTurkish ? 'Gecmis' : 'History', icon: History },
    { to: '/reports', label: isTurkish ? 'Raporlar' : 'Reports', icon: ScrollText },
    { to: '/chat', label: isTurkish ? 'Sohbet' : 'Chat', icon: MessageSquare },
    { to: '/settings', label: isTurkish ? 'Ayarlar' : 'Settings', icon: Settings },
  ]

  return (
    <nav
      className="fixed inset-x-3 z-30 flex items-center justify-between rounded-[28px] border border-[var(--line-soft)] bg-[var(--nav-surface)] px-2 py-2.5 shadow-[var(--shadow-panel)] backdrop-blur-xl sm:inset-x-4 sm:py-3 lg:hidden"
      style={{ bottom: 'max(0.75rem, env(safe-area-inset-bottom, 0.75rem))' }}
    >
      {items.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            cn(
              'flex flex-1 flex-col items-center gap-1 rounded-2xl px-1.5 py-1.5 text-[10px] font-semibold text-[var(--text-muted)] transition sm:px-3 sm:text-[11px]',
              isActive && 'bg-[var(--primary-soft)] text-[var(--text-on-accent)]',
            )
          }
        >
          <Icon className="size-[18px] sm:size-4" />
          <span className="max-w-full truncate">{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
