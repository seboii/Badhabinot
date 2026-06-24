/**
 * Sunucu-taraflı görsel CAPTCHA.
 *
 * Karolar (3×3) sunucuda PNG'ye çizilip `data:image/png` olarak gelir; şekil
 * bilgisi istemciye veri olarak verilmez (bir botun çözmesi için görüntü tanıma
 * gerekir). Doğrulama da sunucuda yapılır: kullanıcı seçimi `POST /auth/captcha/verify`
 * ile gönderilir, doğruysa tek-kullanımlık bir geçiş token'ı döner ve `onVerified`
 * ile üst bileşene iletilir. Kayıt bu token olmadan kabul edilmez.
 */
import { useState, useCallback, useEffect } from 'react'
import { RefreshCw, ShieldCheck } from 'lucide-react'
import { cn } from '@/lib/cn'
import { authApi } from '@/api/auth'

type Status = 'loading' | 'idle' | 'verifying' | 'ok' | 'error'

type Props = {
  isTurkish: boolean
  /** Doğrulama başarılı olunca tek-kullanımlık geçiş token'ı. */
  onVerified: (token: string) => void
  /** Seçim değişince / yeni görev gelince üst token'ı geçersiz kıl. */
  onReset?: () => void
}

export function CaptchaWidget({ isTurkish, onVerified, onReset }: Props) {
  const [captchaId, setCaptchaId] = useState<string | null>(null)
  const [tiles, setTiles] = useState<string[]>([])
  const [promptTr, setPromptTr] = useState('')
  const [promptEn, setPromptEn] = useState('')
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [status, setStatus] = useState<Status>('loading')

  const load = useCallback(async () => {
    setStatus('loading')
    setSelected(new Set())
    onReset?.()
    try {
      const c = await authApi.getCaptcha()
      setCaptchaId(c.captcha_id)
      setTiles(c.tiles)
      setPromptTr(c.prompt_tr)
      setPromptEn(c.prompt_en)
      setStatus('idle')
    } catch {
      setStatus('error')
    }
  }, [onReset])

  // Yalnızca ilk yüklemede challenge çek.
  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function toggleTile(idx: number) {
    if (status === 'loading' || status === 'verifying') return
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
    if (status === 'ok' || status === 'error') {
      setStatus('idle')
      onReset?.()
    }
  }

  async function handleVerify() {
    if (!captchaId || selected.size === 0) return
    setStatus('verifying')
    try {
      const { token } = await authApi.verifyCaptcha(captchaId, [...selected])
      setStatus('ok')
      onVerified(token)
    } catch {
      setStatus('error')
      onReset?.()
      // Yanlış cevap → kısa süre sonra yeni görev getir.
      setTimeout(() => void load(), 1100)
    }
  }

  const shapeName = isTurkish ? promptTr : promptEn

  return (
    <div className="rounded-2xl border border-[var(--line-soft)] bg-[var(--surface-subtle)] p-4 select-none">
      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck size={14} className="text-[var(--text-muted)]" />
          <p className="text-xs font-medium text-[var(--text-muted)]">
            {isTurkish ? 'Robot olmadığınızı doğrulayın' : 'Verify you are not a robot'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          title={isTurkish ? 'Yeni görev' : 'New challenge'}
          className="text-[var(--text-muted)] transition hover:text-[var(--text-strong)]"
        >
          <RefreshCw size={13} className={status === 'loading' ? 'animate-spin' : undefined} />
        </button>
      </div>

      {/* Instruction */}
      <p className="mb-3 text-sm font-semibold text-[var(--text-strong)]">
        {isTurkish ? `Tüm ${shapeName} şekillerine tıklayın` : `Click all ${shapeName}s`}
      </p>

      {/* Grid — sabit küçük genişlik (karolar büyük görünmesin) */}
      <div className="grid grid-cols-3 gap-2 mb-3 max-w-[200px]">
        {tiles.length === 0 && status === 'loading'
          ? Array.from({ length: 9 }).map((_, idx) => (
              <div
                key={idx}
                className="aspect-square animate-pulse rounded-xl bg-[var(--surface-soft)]"
              />
            ))
          : tiles.map((tile, idx) => {
              const isSelected = selected.has(idx)
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => toggleTile(idx)}
                  className={cn(
                    'flex aspect-square items-center justify-center overflow-hidden rounded-xl border-2 transition-all',
                    'bg-[var(--surface-soft)]',
                    isSelected
                      ? 'border-[var(--primary)] bg-[rgba(99,102,241,0.12)] scale-95'
                      : 'border-transparent hover:border-[var(--line-soft)]',
                  )}
                >
                  <img src={tile} alt="" draggable={false} className="size-full object-contain" />
                </button>
              )
            })}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs text-[var(--text-muted)]">
          {status === 'error' && (
            <span className="text-[var(--danger)]">
              {isTurkish ? 'Yanlış, yeniden deneyin.' : 'Incorrect, try again.'}
            </span>
          )}
          {status === 'ok' && (
            <span className="text-[#22c55e]">{isTurkish ? 'Doğrulandı!' : 'Verified!'}</span>
          )}
        </div>
        <button
          type="button"
          onClick={() => void handleVerify()}
          disabled={selected.size === 0 || status === 'verifying' || status === 'loading' || status === 'ok'}
          className={cn(
            'rounded-xl px-4 py-1.5 text-xs font-semibold transition',
            'bg-[var(--primary)] text-white',
            'hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed',
          )}
        >
          {status === 'verifying'
            ? isTurkish ? 'Kontrol...' : 'Checking...'
            : isTurkish ? 'Doğrula' : 'Verify'}
        </button>
      </div>
    </div>
  )
}
