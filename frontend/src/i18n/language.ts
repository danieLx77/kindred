export const SUPPORTED_LANGUAGES = ["pt-BR", "en"] as const;

export type Language = (typeof SUPPORTED_LANGUAGES)[number];

export const DEFAULT_LANGUAGE: Language = "pt-BR";
export const FALLBACK_LANGUAGE: Language = "en";

export const LANGUAGE_STORAGE_KEY = "kindred.language";

export function isSupportedLanguage(value: unknown): value is Language {
  return typeof value === "string" && (SUPPORTED_LANGUAGES as readonly string[]).includes(value);
}

export function readStoredLanguage(): Language | null {
  try {
    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return isSupportedLanguage(stored) ? stored : null;
  } catch {
    return null;
  }
}

export function storeLanguage(language: Language): void {
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  } catch {
    // Ignore storage write errors (e.g. private browsing limits)
  }
}

export function resolveInitialLanguage(): Language {
  const stored = readStoredLanguage();
  if (stored) return stored;

  const browserLanguage = typeof navigator !== "undefined" ? navigator.language : "";
  if (browserLanguage.toLowerCase().startsWith("pt")) return "pt-BR";

  return FALLBACK_LANGUAGE;
}
