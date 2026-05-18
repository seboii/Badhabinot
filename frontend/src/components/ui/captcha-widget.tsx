import { useState, useCallback } from 'react'
import { RefreshCw, ShieldCheck } from 'lucide-react'
import { cn } from '@/lib/cn'

function generateChallenge() {
  const a = Math.floor(Math.random() * 9) + 1
  const b = Math.floor(Math.random() * 9) + 1
  return { a, b, answer: a + b }
}

type Props = {
  isTurkish: boolean
  onValidate: (valid: boolean) => void
}

export function CaptchaWidget({ isTurkish, onValidate }: Props) {
  const [challenge, setChallenge] = useState(generateChallenge)
  const [value, setValue] = useState('')
  const [touched, setTouched] = useState(false)

  const isValid = value !== '' && parseInt(value, 10) === challenge.answer

  const refresh = useCallback(() => {
    setChallenge(generateChallenge())
    setValue('')
    setTouched(false)
    onValidate(false)
  }, [onValidate])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/[^0-9]/g, '').slice(0, 2)
    setValue(raw)
    setTouched(true)
    onValidate(raw !== '' && parseInt(raw, 10) === challenge.answer)
  }

  return (
    <div
      className={cn(
        'rounded-2xl border p-4 transition',
        isValid
          ? 'border-[var(--primary)] bg-[var(--surface-soft)]'
          : 'border-[var(--line-soft)] bg-[var(--surface-subtle)]',
      )}
    >
      <div className="mb-3 flex items-center gap-2">
        <ShieldCheck size={14} className="text-[var(--text-muted)]" />
        <p className="text-xs text-[var(--text-muted)]">
          {isTurkish ? 'Robot olmadığınızı doğrulayın' : 'Verify you are not a robot'}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <span className="select-none rounded-xl bg-[var(--surface-soft)] px-4 py-2 font-mono text-sm font-semibold tracking-widest text-[var(--text-strong)]">
          {challenge.a} + {challenge.b} = ?
        </span>

        <input
          type="text"
          inputMode="numeric"
          maxLength={2}
          value={value}
          onChange={handleChange}
          placeholder="?"
          aria-label={isTurkish ? 'Cevap' : 'Answer'}
          className={cn(
            'h-10 w-16 rounded-xl border bg-[var(--surface-subtle)] px-3 text-center text-sm font-semibold outline-none transition',
            'focus:border-[var(--primary)]',
            touched && !isValid && value !== '' && 'border-[var(--danger)] text-[var(--danger)]',
            isValid && 'border-[var(--primary)] text-[var(--primary)]',
            !touched || value === '' ? 'border-[var(--line-soft)]' : '',
          )}
        />

        <button
          type="button"
          onClick={refresh}
          title={isTurkish ? 'Yeni soru' : 'New challenge'}
          className="text-[var(--text-muted)] transition hover:text-[var(--text-strong)]"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {touched && !isValid && value !== '' && (
        <p className="mt-2 text-xs text-[var(--danger)]">
          {isTurkish ? 'Yanlış cevap, tekrar deneyin.' : 'Wrong answer, please try again.'}
        </p>
      )}
    </div>
  )
}
