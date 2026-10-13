import { useTranslation } from 'react-i18next'
import type { Language } from '../i18n'

const OPTIONS: { language: Language; labelKey: 'language.pt' | 'language.en' }[] = [
  { language: 'pt-BR', labelKey: 'language.pt' },
  { language: 'en', labelKey: 'language.en' },
]

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation()
  const current = i18n.resolvedLanguage

  return (
    <div className="language-switcher" role="group" aria-label={t('language.label')}>
      {OPTIONS.map(({ language, labelKey }) => (
        <button
          key={language}
          type="button"
          className="language-switcher__button"
          lang={language}
          aria-pressed={current === language}
          onClick={() => void i18n.changeLanguage(language)}
        >
          {t(labelKey)}
        </button>
      ))}
    </div>
  )
}
