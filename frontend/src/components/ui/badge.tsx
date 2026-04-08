import type { HTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

type BadgeVariant = 'primary' | 'success' | 'warning' | 'neutral' | 'danger' | 'info'

const variantMap: Record<BadgeVariant, string> = {
  primary: 'bg-[var(--primary-soft)] text-[var(--primary)]',
  success: 'bg-[var(--success-soft)] text-[var(--success)]',
  warning: 'bg-[var(--warning-soft)] text-[var(--warning)]',
  neutral: 'bg-[var(--surface-muted)] text-[var(--text-muted)]',
  danger: 'bg-[var(--danger-soft)] text-[var(--danger)]',
  info: 'bg-[var(--info-soft)] text-[var(--info)]',
}

export function Badge({
  className,
  children,
  variant = 'neutral',
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold tracking-wide',
        variantMap[variant],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  )
}
