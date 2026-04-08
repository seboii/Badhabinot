import { createContext, useContext, useEffect, useMemo, useState, type PropsWithChildren } from 'react'

export type AppLanguage = 'en' | 'tr'

type LanguageContextValue = {
  language: AppLanguage
  setLanguage: (language: AppLanguage) => void
  toggleLanguage: () => void
  isTurkish: boolean
}

const STORAGE_KEY = 'badhabinot.language'

function resolveInitialLanguage(): AppLanguage {
  if (typeof window === 'undefined') {
    return 'en'
  }

  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored === 'en' || stored === 'tr') {
    return stored
  }

  return window.navigator.language.toLowerCase().startsWith('tr') ? 'tr' : 'en'
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined)

export function LanguageProvider({ children }: PropsWithChildren) {
  const [language, setLanguage] = useState<AppLanguage>(() => resolveInitialLanguage())

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, language)
  }, [language])

  const value = useMemo<LanguageContextValue>(
    () => ({
      language,
      setLanguage,
      toggleLanguage: () => setLanguage((current) => (current === 'en' ? 'tr' : 'en')),
      isTurkish: language === 'tr',
    }),
    [language],
  )

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const context = useContext(LanguageContext)

  if (!context) {
    throw new Error('useLanguage must be used inside LanguageProvider')
  }

  return context
}
