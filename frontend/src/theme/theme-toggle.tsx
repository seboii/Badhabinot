import { MoonStar, SunMedium } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useLanguage } from '@/i18n/language-provider'
import { useTheme } from '@/theme/theme-provider'

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const { isTurkish } = useLanguage()
  const isDark = theme === 'dark'

  return (
    <Button
      variant="outline"
      size="sm"
      className="min-w-[126px] justify-center rounded-full bg-[var(--surface-soft)]"
      iconLeft={isDark ? <SunMedium className="size-4" /> : <MoonStar className="size-4" />}
      onClick={toggleTheme}
      type="button"
    >
      {isDark ? (isTurkish ? 'Acik tema' : 'Light mode') : isTurkish ? 'Koyu tema' : 'Dark mode'}
    </Button>
  )
}
