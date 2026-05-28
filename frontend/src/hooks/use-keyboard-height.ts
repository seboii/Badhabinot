import { useEffect, useState } from 'react'

/**
 * Detects whether the virtual keyboard is open by comparing visualViewport height
 * to window.innerHeight. When the keyboard opens it shrinks the visual viewport.
 *
 * Returns true when keyboard is visible (viewport < 75% of inner height).
 */
export function useKeyboardHeight(): boolean {
  const [keyboardOpen, setKeyboardOpen] = useState(false)

  useEffect(() => {
    const vv = window.visualViewport
    if (!vv) return

    const handleResize = () => {
      setKeyboardOpen(vv.height < window.innerHeight * 0.75)
    }

    vv.addEventListener('resize', handleResize)
    return () => vv.removeEventListener('resize', handleResize)
  }, [])

  return keyboardOpen
}
