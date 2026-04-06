import { LoaderCircle } from 'lucide-react'

export function InlineSpinner() {
  return <LoaderCircle className="size-4 animate-spin text-[var(--primary)]" />
}

export function LoadingCard({ message = 'Loading data' }: { message?: string }) {
  return (
    <div className="flex min-h-[220px] items-center justify-center rounded-[28px] border border-[var(--line-soft)] bg-[var(--surface)] p-6 text-sm text-[var(--text-muted)]">
      <div className="flex items-center gap-3">
        <InlineSpinner />
        <span>{message}</span>
      </div>
    </div>
  )
}

export function LoadingScreen({ message = 'Loading workspace' }: { message?: string }) {
  return (
    <div className="app-shell-grid flex min-h-screen items-center justify-center px-6">
      <div className="rounded-[32px] border border-[var(--line-soft)] bg-[var(--surface)] px-8 py-7 shadow-[var(--shadow-panel)]">
        <div className="flex items-center gap-4">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-[var(--primary-soft)]">
            <LoaderCircle className="size-5 animate-spin text-[var(--primary)]" />
          </div>
          <div>
            <p className="text-sm font-semibold text-[var(--text-strong)]">BADHABINOT</p>
            <p className="text-sm text-[var(--text-muted)]">{message}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
