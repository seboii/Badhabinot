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
