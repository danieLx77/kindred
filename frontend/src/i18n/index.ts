import i18next, { type i18n as I18nInstance } from 'i18next'
import en from './locales/en'
import ptBR from './locales/pt-BR'
import {
  FALLBACK_LANGUAGE,
  SUPPORTED_LANGUAGES,
  isSupportedLanguage,
  resolveInitialLanguage,
  storeLanguage,
  type Language,
} from './language'

export * from './language'

function syncDocumentLanguage(language: string) {
  if (typeof document !== 'undefined') {
    document.documentElement.lang = language
  }
}

export function createI18n(initialLanguage?: Language): I18nInstance {
  const instance = i18next.createInstance()
  const language = initialLanguage ?? resolveInitialLanguage()

  instance.init({
    resources: {
      'pt-BR': { translation: ptBR },
      en: { translation: en },
    },
    lng: language,
    fallbackLng: FALLBACK_LANGUAGE,
    supportedLngs: [...SUPPORTED_LANGUAGES],
    initAsync: false,
    interpolation: { escapeValue: false }, // o React já escapa
    react: { useSuspense: false },
  })

  syncDocumentLanguage(language)

  instance.on('languageChanged', (next) => {
    if (isSupportedLanguage(next)) {
      storeLanguage(next)
    }
    syncDocumentLanguage(next)
  })

  return instance
}
