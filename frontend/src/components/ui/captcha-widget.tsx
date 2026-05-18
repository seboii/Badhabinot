/**
 * Custom image-based CAPTCHA — no external services required.
 * Shows a 3×3 grid of colored shape tiles.
 * The user must select all tiles that match the challenge shape.
 */
import { useState, useCallback, useMemo } from 'react'
import { RefreshCw, ShieldCheck } from 'lucide-react'
import { cn } from '@/lib/cn'

// ─── Shape renderers ──────────────────────────────────────────────────────────

type Shape = 'circle' | 'square' | 'triangle' | 'diamond' | 'star'

const SHAPES: Shape[] = ['circle', 'square', 'triangle', 'diamond', 'star']

const SHAPE_LABELS: Record<Shape, { tr: string; en: string }> = {
  circle:   { tr: 'daire',    en: 'circle'   },
  square:   { tr: 'kare',     en: 'square'   },
  triangle: { tr: 'üçgen',   en: 'triangle' },
  diamond:  { tr: 'baklava',  en: 'diamond'  },
  star:     { tr: 'yıldız',  en: 'star'     },
}

const TILE_COLORS = [
  '#6366f1', // indigo
  '#ec4899', // pink
  '#14b8a6', // teal
  '#f59e0b', // amber
  '#22c55e', // green
  '#ef4444', // red
  '#8b5cf6', // violet
  '#0ea5e9', // sky
  '#f97316', // orange
]

function ShapeSvg({ shape, color }: { shape: Shape; color: string }) {
  const size = 44
  const cx = size / 2
  const cy = size / 2
  const r = 16

  switch (shape) {
    case 'circle':
      return (
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle cx={cx} cy={cy} r={r} fill={color} />
        </svg>
      )
    case 'square':
      return (
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <rect x={cx - r} y={cy - r} width={r * 2} height={r * 2} rx={4} fill={color} />
        </svg>
      )
    case 'triangle':
      return (
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <polygon
            points={`${cx},${cy - r} ${cx + r},${cy + r} ${cx - r},${cy + r}`}
            fill={color}
          />
        </svg>
      )
    case 'diamond':
      return (
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <polygon
            points={`${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}`}
            fill={color}
          />
        </svg>
      )
    case 'star':
      return (
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <polygon
            points={starPoints(cx, cy, r, r * 0.45, 5)}
            fill={color}
          />
        </svg>
      )
  }
}

function starPoints(cx: number, cy: number, outerR: number, innerR: number, points: number) {
  const pts: string[] = []
  for (let i = 0; i < points * 2; i++) {
    const angle = (Math.PI / points) * i - Math.PI / 2
    const r = i % 2 === 0 ? outerR : innerR
    pts.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`)
  }
  return pts.join(' ')
}

// ─── Challenge generation ─────────────────────────────────────────────────────

type Tile = { shape: Shape; color: string }

function generateChallenge(): { tiles: Tile[]; targetShape: Shape; correctIndices: Set<number> } {
  const targetShape = SHAPES[Math.floor(Math.random() * SHAPES.length)]
  const otherShapes = SHAPES.filter((s) => s !== targetShape)
  const correctCount = 3 + Math.floor(Math.random() * 2) // 3 or 4 correct

  const tiles: Tile[] = []
  const correctIndices = new Set<number>()

  // Place correct tiles
  const positions = shuffle([0, 1, 2, 3, 4, 5, 6, 7, 8])
  for (let i = 0; i < correctCount; i++) {
    correctIndices.add(positions[i])
  }

  // Fill all 9 tiles
  let colorIdx = 0
  for (let i = 0; i < 9; i++) {
    const shape = correctIndices.has(i)
      ? targetShape
      : otherShapes[Math.floor(Math.random() * otherShapes.length)]
    const color = TILE_COLORS[colorIdx % TILE_COLORS.length]
    colorIdx++
    tiles.push({ shape, color })
  }

  return { tiles, targetShape, correctIndices }
}

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

// ─── Component ────────────────────────────────────────────────────────────────

type Props = {
  isTurkish: boolean
  onValidate: (valid: boolean) => void
}

export function CaptchaWidget({ isTurkish, onValidate }: Props) {
  const [challenge, setChallenge] = useState(generateChallenge)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [submitted, setSubmitted] = useState(false)

  const { tiles, targetShape, correctIndices } = challenge

  const isCorrect = useMemo(() => {
    if (selected.size !== correctIndices.size) return false
    for (const idx of correctIndices) {
      if (!selected.has(idx)) return false
    }
    return true
  }, [selected, correctIndices])

  const refresh = useCallback(() => {
    setChallenge(generateChallenge())
    setSelected(new Set())
    setSubmitted(false)
    onValidate(false)
  }, [onValidate])

  function toggleTile(idx: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
    setSubmitted(false)
    onValidate(false)
  }

  function handleVerify() {
    setSubmitted(true)
    if (isCorrect) {
      onValidate(true)
    } else {
      // Auto-refresh after wrong answer
      setTimeout(refresh, 900)
    }
  }

  const shapeName = isTurkish ? SHAPE_LABELS[targetShape].tr : SHAPE_LABELS[targetShape].en

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
          onClick={refresh}
          title={isTurkish ? 'Yeni görev' : 'New challenge'}
          className="text-[var(--text-muted)] transition hover:text-[var(--text-strong)]"
        >
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Instruction */}
      <p className="mb-3 text-sm font-semibold text-[var(--text-strong)]">
        {isTurkish
          ? `Tüm ${shapeName} şekillerine tıklayın`
          : `Click all ${shapeName}s`}
      </p>

      {/* Grid */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        {tiles.map((tile, idx) => {
          const isSelected = selected.has(idx)
          const showResult = submitted
          const isRight = correctIndices.has(idx)
          return (
            <button
              key={idx}
              type="button"
              onClick={() => toggleTile(idx)}
              className={cn(
                'flex aspect-square items-center justify-center rounded-xl border-2 transition-all',
                'bg-[var(--surface-soft)]',
                isSelected && !showResult && 'border-[var(--primary)] bg-[rgba(99,102,241,0.12)] scale-95',
                !isSelected && !showResult && 'border-transparent hover:border-[var(--line-soft)]',
                showResult && isSelected && isRight && 'border-[#22c55e] bg-[rgba(34,197,94,0.12)]',
                showResult && isSelected && !isRight && 'border-[var(--danger)] bg-[rgba(239,68,68,0.12)]',
                showResult && !isSelected && isRight && 'border-[#f59e0b] bg-[rgba(245,158,11,0.10)]',
                showResult && !isSelected && !isRight && 'border-transparent',
              )}
            >
              <ShapeSvg shape={tile.shape} color={tile.color} />
            </button>
          )
        })}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs text-[var(--text-muted)]">
          {submitted && !isCorrect && (
            <span className="text-[var(--danger)]">
              {isTurkish ? 'Yanlış, yeniden deneyin.' : 'Incorrect, try again.'}
            </span>
          )}
          {submitted && isCorrect && (
            <span className="text-[#22c55e]">
              {isTurkish ? 'Doğrulandı!' : 'Verified!'}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={handleVerify}
          disabled={selected.size === 0}
          className={cn(
            'rounded-xl px-4 py-1.5 text-xs font-semibold transition',
            'bg-[var(--primary)] text-white',
            'hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed',
          )}
        >
          {isTurkish ? 'Doğrula' : 'Verify'}
        </button>
      </div>
    </div>
  )
}
