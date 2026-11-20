import { useTranslation } from "react-i18next";
import brazilFlag from "../assets/flags/br.svg";
import unitedStatesFlag from "../assets/flags/us.svg";
import type { Language } from "../i18n";

const OPTIONS = [
  { language: "pt-BR", labelKey: "language.pt", flag: brazilFlag },
  { language: "en", labelKey: "language.en", flag: unitedStatesFlag },
] as const satisfies ReadonlyArray<{
  language: Language;
  labelKey: "language.pt" | "language.en";
  flag: string;
}>;

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const current = i18n.resolvedLanguage;

  return (
    <div className="language-switcher" role="group" aria-label={t("language.label")}>
      {OPTIONS.map(({ language, labelKey, flag }) => (
        <button
          key={language}
          type="button"
          className="language-switcher__button"
          aria-label={t(labelKey)}
          aria-pressed={current === language}
          onClick={() => void i18n.changeLanguage(language)}
        >
          <img src={flag} alt="" width={28} height={21} />
        </button>
      ))}
    </div>
  );
}
