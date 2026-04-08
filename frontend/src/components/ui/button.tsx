import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { LoaderCircle } from 'lucide-react'
import { cn } from '@/lib/cn'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'
type ButtonSize = 'md' | 'sm' | 'lg'

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-[var(--primary)] text-[var(--text-on-accent)] shadow-[var(--shadow-accent)] hover:bg-[var(--primary-hover)]',
  secondary: 'bg-[var(--surface-hover)] text-[var(--text-strong)] hover:bg-[var(--surface-muted)]',
  ghost: 'bg-transparent text-[var(--text-muted)] hover:bg-[var(--surface-soft)] hover:text-[var(--text-strong)]',
  danger: 'bg-[var(--danger)] text-[var(--text-on-accent)] hover:bg-[#e11d48]',
  outline:
    'border border-[var(--line-strong)] bg-transparent text-[var(--text-strong)] hover:border-[var(--primary)] hover:bg-[var(--primary-soft)]',
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'h-10 px-3 text-sm',
  md: 'h-11 px-4 text-sm',
  lg: 'h-12 px-5 text-sm',
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  size?: ButtonSize
  loading?: boolean
  iconLeft?: ReactNode
}

export function Button({
  className,
  variant = 'primary',
  size = 'md',
  loading = false,
  iconLeft,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-2xl border border-transparent font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--primary)] disabled:cursor-not-allowed disabled:opacity-50',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <LoaderCircle className="size-4 animate-spin" /> : iconLeft}
      {children}
    </button>
  )
}
