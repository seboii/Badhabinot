import { useRef, useState } from 'react'
import { X, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useLanguage } from '@/i18n/language-provider'
import { KVKK_SECTIONS_TR, KVKK_SECTIONS_EN } from '@/content/kvkk'

type KvkkModalProps = {
  isOpen: boolean
  onConfirm: () => void
  onClose: () => void
}

export function KvkkModal({ isOpen, onConfirm, onClose }: KvkkModalProps) {
  const { isTurkish } = useLanguage()
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false)
  const scrollRef = useRef<HTMLDivElement | null>(null)

  const sections = isTurkish ? KVKK_SECTIONS_TR : KVKK_SECTIONS_EN

  if (!isOpen) return null

  function handleScroll(e: React.UIEvent<HTMLDivElement>) {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget
    if (scrollTop + clientHeight >= scrollHeight - 24) {
      setHasScrolledToBottom(true)
    }
  }

  function handleConfirm() {
    onConfirm()
    setHasScrolledToBottom(false)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="relative flex w-full max-w-2xl flex-col rounded-[32px] border border-[var(--line-soft)] bg-[var(--surface-soft)] shadow-2xl"
        style={{ maxHeight: '90vh' }}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-[var(--line-soft)] p-6 pb-5">
          <div className="flex items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl bg-[var(--primary-soft)]">
              <ShieldCheck className="size-5 text-[var(--primary)]" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">
                {isTurkish ? 'KVKK Aydınlatma Metni' : 'Data Protection Disclosure'}
              </h2>
              <p className="text-sm text-[var(--text-muted)]">
                {isTurkish
                  ? 'Devam etmek için lütfen metni okuyun'
                  : 'Please read the full text to continue'}
              </p>
            </div>
          </div>
          <button
            className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[var(--surface-hover)] text-[var(--text-muted)] transition hover:text-white"
            onClick={onClose}
            aria-label={isTurkish ? 'Kapat' : 'Close'}
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Scrollable body */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-6 text-sm leading-7 text-[var(--text-muted)]"
          style={{ minHeight: 0 }}
          onScroll={handleScroll}
        >
          <div className="space-y-6">
            {sections.map((section, i) => (
              <section key={i}>
                <h3 className="mb-2 text-sm font-semibold text-[var(--text-strong)]">
                  {section.heading}
                </h3>
                <div className="space-y-1">
                  {section.body.map((line, j) => (
                    <p key={j}>{line}</p>
                  ))}
                </div>
              </section>
            ))}
          </div>

          {/* Scroll nudge — fades out after scroll */}
          {!hasScrolledToBottom && (
            <div className="pointer-events-none sticky bottom-0 mt-4 flex justify-center pb-1">
              <span className="rounded-full bg-[var(--surface-muted)] px-3 py-1 text-xs text-[var(--text-soft)]">
                {isTurkish ? '↓ Devam etmek için aşağı kaydırın' : '↓ Scroll down to continue'}
              </span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-[var(--line-soft)] p-6 pt-5">
          {!hasScrolledToBottom && (
            <p className="mb-3 text-center text-xs text-[var(--text-muted)]">
              {isTurkish
                ? 'Butonu etkinleştirmek için metnin sonuna gidin.'
                : 'Scroll to the bottom to enable the button.'}
            </p>
          )}
          <div className="flex gap-3">
            <Button variant="secondary" className="flex-1" onClick={onClose}>
              {isTurkish ? 'Kapat' : 'Close'}
            </Button>
            <Button
              variant="primary"
              className="flex-1"
              disabled={!hasScrolledToBottom}
              onClick={handleConfirm}
            >
              {isTurkish ? 'Okudum, Anladım' : 'I have read and understood'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
