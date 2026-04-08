import type { LucideIcon } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'

type EmptyStateProps = {
  icon: LucideIcon
  title: string
  description: string
}

export function EmptyState({ icon: Icon, title, description }: EmptyStateProps) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
        <div className="flex size-14 items-center justify-center rounded-2xl bg-[rgba(255,255,255,0.05)]">
          <Icon className="size-6 text-[var(--text-muted)]" />
        </div>
        <div className="space-y-2">
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <p className="max-w-md text-sm text-[var(--text-muted)]">{description}</p>
        </div>
      </CardContent>
    </Card>
  )
}

