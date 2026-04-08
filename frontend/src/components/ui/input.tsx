import type { InputHTMLAttributes } from 'react'
import { cn } from '@/lib/cn'

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string
  hint?: string
  error?: string
}

export function Input({ label, hint, error, className, ...props }: InputProps) {
  const control = (
    <input
      className={cn(
        'h-12 w-full rounded-2xl border border-[var(--line-soft)] bg-[var(--surface-subtle)] px-4 text-sm text-[var(--text-strong)] outline-none transition placeholder:text-[var(--text-soft)] focus:border-[var(--primary)] focus:bg-[var(--surface-soft)]',
        error && 'border-[var(--danger)]',
        className,
      )}
      {...props}
    />
  )

  if (!label) {
    return control
  }

  return (
    <label className="flex flex-col gap-2">
      <span className="text-sm font-medium text-[var(--text-strong)]">{label}</span>
      {control}
      {hint ? <span className="text-xs text-[var(--text-muted)]">{hint}</span> : null}
      {error ? <span className="text-xs text-[var(--danger)]">{error}</span> : null}
    </label>
  )
}
