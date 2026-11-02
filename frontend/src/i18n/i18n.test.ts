import { describe, expect, it, vi } from "vitest";
import {
  LANGUAGE_STORAGE_KEY,
  createI18n,
  isSupportedLanguage,
  readStoredLanguage,
  resolveInitialLanguage,
} from "./index";
import en from "./locales/en";
import ptBR from "./locales/pt-BR";

function flatten(value: Record<string, unknown>, prefix = ""): Record<string, string> {
  return Object.entries(value).reduce<Record<string, string>>((acc, [key, entry]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof entry === "string") {
      acc[path] = entry;
    } else {
      Object.assign(acc, flatten(entry as Record<string, unknown>, path));
    }
    return acc;
  }, {});
}

function placeholders(text: string): string[] {
  return [...text.matchAll(/\{\{\s*(\w+)\s*\}\}/g)].map((match) => match[1]).sort();
}

describe("dicionários", () => {
  const ptEntries = flatten(ptBR);
  const enEntries = flatten(en);

  it("têm exatamente as mesmas chaves em PT-BR e EN", () => {
    expect(Object.keys(enEntries).sort()).toEqual(Object.keys(ptEntries).sort());
  });

  it("não têm textos vazios", () => {
    for (const [key, text] of [...Object.entries(ptEntries), ...Object.entries(enEntries)]) {
      expect(text.trim(), key).not.toBe("");
    }
  });

  it("usam os mesmos placeholders de interpolação nas duas línguas", () => {
    for (const key of Object.keys(ptEntries)) {
      expect(placeholders(enEntries[key]), key).toEqual(placeholders(ptEntries[key]));
    }
  });
});

describe("idioma", () => {
  it("reconhece apenas pt-BR e en como suportados", () => {
    expect(isSupportedLanguage("pt-BR")).toBe(true);
    expect(isSupportedLanguage("en")).toBe(true);
    expect(isSupportedLanguage("pt")).toBe(false);
    expect(isSupportedLanguage("fr")).toBe(false);
    expect(isSupportedLanguage(null)).toBe(false);
  });

  it("lê a preferência guardada só se for válida", () => {
    expect(readStoredLanguage()).toBeNull();

    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "en");
    expect(readStoredLanguage()).toBe("en");

    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "xx");
    expect(readStoredLanguage()).toBeNull();
  });

  it("resolve o idioma inicial: guardado → browser → inglês", () => {
    const browser = vi.spyOn(window.navigator, "language", "get");

    browser.mockReturnValue("en-US");
    expect(resolveInitialLanguage()).toBe("en");

    browser.mockReturnValue("pt-BR");
    expect(resolveInitialLanguage()).toBe("pt-BR");

    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "en");
    expect(resolveInitialLanguage()).toBe("en");
  });
});

describe("createI18n", () => {
  it("traduz com interpolação e sincroniza o <html lang>", () => {
    const i18n = createI18n("pt-BR");

    expect(i18n.t("footer.copyright", { year: 2026 })).toBe("© 2026 Kindred");
    expect(document.documentElement.lang).toBe("pt-BR");
  });

  it("guarda o idioma ao mudar, mas não guarda o idioma inicial", async () => {
    const i18n = createI18n("pt-BR");
    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBeNull();

    await i18n.changeLanguage("en");

    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe("en");
    expect(i18n.t("nav.home")).toBe("Home");
    expect(document.documentElement.lang).toBe("en");
  });

  it("instâncias diferentes não partilham estado", async () => {
    const first = createI18n("pt-BR");
    const second = createI18n("pt-BR");

    await first.changeLanguage("en");

    expect(first.t("nav.home")).toBe("Home");
    expect(second.t("nav.home")).toBe("Início");
  });
});
