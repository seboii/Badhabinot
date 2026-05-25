import type { ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { Button } from '@/components/ui/button'

type ConfirmDialogProps = {
  isOpen: boolean
  title: string
  description?: ReactNode
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'default'
  loading?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  isOpen,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) return null

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onCancel} />

      {/* Panel */}
      <div className="relative w-full max-w-md rounded-[24px] border border-[var(--line-soft)] bg-[var(--surface-soft)] p-5 shadow-xl sm:rounded-3xl sm:p-6" style={{ maxHeight: '90svh', overflowY: 'auto' }}>
        <h2 id="confirm-dialog-title" className="text-base font-semibold text-[var(--text-strong)]">
          {title}
        </h2>
        {description ? (
          <div className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{description}</div>
        ) : null}
        <div className="mt-5 flex flex-col-reverse gap-2 sm:mt-6 sm:flex-row sm:justify-end sm:gap-3">
          <Button variant="secondary" onClick={onCancel} disabled={loading} className="w-full sm:w-auto">
            {cancelLabel}
          </Button>
          <Button variant={variant === 'danger' ? 'danger' : 'primary'} loading={loading} onClick={onConfirm} className="w-full sm:w-auto">
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
