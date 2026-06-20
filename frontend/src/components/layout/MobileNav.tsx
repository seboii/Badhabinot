import { History, LayoutDashboard, MessageSquare, ScrollText, Settings, ShieldCheck } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/cn'
import { useAuth } from '@/hooks/use-auth'
import { useLanguage } from '@/i18n/language-provider'
import { useKeyboardHeight } from '@/hooks/use-keyboard-height'

export function MobileNav() {
  const { isTurkish } = useLanguage()
  const { isAdmin } = useAuth()
  const keyboardOpen = useKeyboardHeight()
  const items = [
    { to: '/dashboard', label: isTurkish ? 'Panel' : 'Dashboard', icon: LayoutDashboard },
    { to: '/history', label: isTurkish ? 'Gecmis' : 'History', icon: History },
    { to: '/reports', label: isTurkish ? 'Raporlar' : 'Reports', icon: ScrollText },
    { to: '/chat', label: isTurkish ? 'Sohbet' : 'Chat', icon: MessageSquare },
    { to: '/settings', label: isTurkish ? 'Ayarlar' : 'Settings', icon: Settings },
    ...(isAdmin ? [{ to: '/admin', label: isTurkish ? 'Yonetim' : 'Admin', icon: ShieldCheck }] : []),
  ]

  return (
    <nav
      className={cn(
        'fixed inset-x-2 z-30 flex items-center justify-between rounded-[24px] border border-[var(--line-soft)] bg-[var(--nav-surface)] px-1 py-2 shadow-[var(--shadow-panel)] backdrop-blur-xl transition-transform sm:inset-x-4 sm:rounded-[28px] sm:px-2 sm:py-2.5 lg:hidden',
        keyboardOpen && 'translate-y-[200%]',
      )}
      style={{ bottom: 'max(0.75rem, env(safe-area-inset-bottom, 0.75rem))' }}
    >
      {items.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            cn(
              'flex flex-1 flex-col items-center gap-0.5 rounded-xl px-1 py-1.5 text-[9px] font-semibold text-[var(--text-muted)] transition sm:gap-1 sm:rounded-2xl sm:px-2.5 sm:py-1.5 sm:text-[11px]',
              isActive && 'bg-[var(--primary-soft)] text-[var(--text-on-accent)]',
            )
          }
        >
          <Icon className="size-[17px] sm:size-[18px]" />
          <span className="max-w-full truncate leading-tight">{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
