import { useEffect, useState } from 'react'

type Breakpoint = 'mobile' | 'tablet' | 'desktop'

function debounce<T extends (...args: Parameters<T>) => ReturnType<T>>(fn: T, ms: number): (...args: Parameters<T>) => void {
  let id: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(id)
    id = setTimeout(() => fn(...args), ms)
  }
}

function getBreakpoint(): Breakpoint {
  if (typeof window === 'undefined') return 'desktop'
  if (window.innerWidth >= 1024) return 'desktop'
  if (window.innerWidth >= 640) return 'tablet'
  return 'mobile'
}

export function useBreakpoint() {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>(getBreakpoint)

  useEffect(() => {
    const check = () => setBreakpoint(getBreakpoint())
    const debounced = debounce(check, 250)
    window.addEventListener('resize', debounced)
    return () => window.removeEventListener('resize', debounced)
  }, [])

  return {
    breakpoint,
    isMobile: breakpoint === 'mobile',
    isTablet: breakpoint === 'tablet',
    isDesktop: breakpoint === 'desktop',
  }
}
