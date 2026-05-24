import { Link } from 'react-router-dom'
import { ChevronLeft, ShieldCheck } from 'lucide-react'
import { useLanguage } from '@/i18n/language-provider'
import { KVKK_SECTIONS_TR, KVKK_SECTIONS_EN } from '@/content/kvkk'

export function KvkkPage() {
  const { isTurkish } = useLanguage()
  const sections = isTurkish ? KVKK_SECTIONS_TR : KVKK_SECTIONS_EN

  return (
    <div className="min-h-screen bg-[var(--bg-base)] px-5 py-10 md:px-8">
      <div className="mx-auto max-w-3xl">
        <Link
          to="/"
          className="mb-8 inline-flex items-center gap-2 text-sm text-[var(--text-muted)] transition hover:text-[var(--text-strong)]"
        >
          <ChevronLeft size={14} />
          {isTurkish ? 'Geri dön' : 'Go back'}
        </Link>

        <div className="mb-8 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-2xl bg-[var(--primary)] bg-opacity-10">
            <ShieldCheck size={20} className="text-[var(--primary)]" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-strong)]">
              {isTurkish ? 'KVKK Aydınlatma Metni' : 'Data Protection Disclosure'}
            </h1>
            <p className="text-sm text-[var(--text-muted)]">
              {isTurkish ? '6698 sayılı Kişisel Verilerin Korunması Kanunu' : 'Law No. 6698 on the Protection of Personal Data'}
            </p>
          </div>
        </div>

        <div className="space-y-8 text-sm leading-7 text-[var(--text-muted)]">
          {sections.map((section, i) => (
            <section key={i}>
              <h2 className="mb-3 text-base font-semibold text-[var(--text-strong)]">
                {section.heading}
              </h2>
              <div className="space-y-1">
                {section.body.map((line, j) => (
                  <p key={j}>{line}</p>
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  )
}
