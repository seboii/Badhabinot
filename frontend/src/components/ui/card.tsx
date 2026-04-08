import type { HTMLAttributes, PropsWithChildren } from 'react'
import { cn } from '@/lib/cn'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface)] shadow-[var(--shadow-soft)] backdrop-blur-xl',
        className,
      )}
      {...props}
    />
  )
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('flex items-start justify-between gap-4 p-6 pb-0', className)} {...props} />
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('p-6', className)} {...props} />
}

export function CardTitle({ className, children }: PropsWithChildren<{ className?: string }>) {
  return <h2 className={cn('text-lg font-bold tracking-tight text-[var(--text-strong)]', className)}>{children}</h2>
}

export function CardDescription({ className, children }: PropsWithChildren<{ className?: string }>) {
  return <p className={cn('text-sm text-[var(--text-muted)]', className)}>{children}</p>
}
