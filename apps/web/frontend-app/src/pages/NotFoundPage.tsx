import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-5">
      <div className="w-full max-w-xl rounded-[32px] border border-[var(--line-soft)] bg-[var(--surface)] p-8 text-center shadow-[var(--shadow-panel)]">
        <div className="mx-auto flex size-16 items-center justify-center rounded-3xl bg-[var(--primary-soft)]">
          <Compass className="size-7 text-[var(--primary)]" />
        </div>
        <h1 className="mt-6 text-3xl font-bold text-[var(--text-strong)]">Route not found</h1>
        <p className="mt-3 text-sm leading-6 text-[var(--text-muted)]">
          The page you requested does not exist in the current BADHABINOT frontend route map.
        </p>
        <div className="mt-8 flex justify-center">
          <Link to="/">
            <Button>Return to workspace</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
