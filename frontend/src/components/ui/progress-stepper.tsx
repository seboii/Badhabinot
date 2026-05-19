import { Check } from 'lucide-react'
import { cn } from '@/lib/cn'

type Step = {
  title: string
}

export function ProgressStepper({ steps, currentStep }: { steps: Step[]; currentStep: number }) {
  const progressPct = ((currentStep - 1) / (steps.length - 1)) * 100

  return (
    <div className="w-full">
      <div className="relative flex items-center justify-between">
        {/* Track */}
        <div className="absolute inset-x-0 top-4 h-0.5 bg-[var(--line-soft)]" />
        {/* Fill */}
        <div
          className="absolute top-4 h-0.5 bg-[var(--primary)] transition-all duration-500"
          style={{ width: `${progressPct}%`, left: 0 }}
        />

        {steps.map((step, index) => {
          const stepNumber = index + 1
          const isDone = stepNumber < currentStep
          const isActive = stepNumber === currentStep

          return (
            <div key={stepNumber} className="relative flex flex-col items-center gap-2">
              <div
                className={cn(
                  'relative z-10 flex size-8 items-center justify-center rounded-full border-2 text-xs font-bold transition-all duration-300',
                  isDone
                    ? 'border-[var(--primary)] bg-[var(--primary)] text-white'
                    : isActive
                      ? 'border-[var(--primary)] bg-[var(--surface-soft)] text-[var(--primary)]'
                      : 'border-[var(--line-soft)] bg-[var(--surface-soft)] text-[var(--text-muted)]',
                )}
              >
                {isDone ? <Check className="size-4" /> : stepNumber}
              </div>
              <span
                className={cn(
                  'whitespace-nowrap text-xs font-medium transition-colors duration-300',
                  isActive ? 'text-white' : 'text-[var(--text-muted)]',
                )}
              >
                {step.title}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
