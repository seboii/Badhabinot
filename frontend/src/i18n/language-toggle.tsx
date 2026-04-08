import { Languages } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useLanguage } from '@/i18n/language-provider'

export function LanguageToggle() {
  const { language, toggleLanguage } = useLanguage()

  return (
    <Button
      variant="outline"
      size="sm"
      className="min-w-[126px] justify-center rounded-full bg-[var(--surface-soft)]"
      iconLeft={<Languages className="size-4" />}
      onClick={toggleLanguage}
      type="button"
    >
      {language === 'en' ? 'Turkce' : 'English'}
    </Button>
  )
}
