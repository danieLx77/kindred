import { screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LANGUAGE_STORAGE_KEY } from "../i18n";
import { renderApp } from "../test/renderApp";

function languageGroup(name: "Idioma" | "Language") {
  return within(screen.getByRole("group", { name }));
}

function mockBrowserLanguage(language: string) {
  vi.spyOn(window.navigator, "language", "get").mockReturnValue(language);
}

describe("seletor de idioma", () => {
  it("oferece Português e English e marca o idioma ativo", () => {
    renderApp({ language: "pt-BR" });
    const group = languageGroup("Idioma");

    expect(group.getByRole("button", { name: "Português" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(group.getByRole("button", { name: "English" })).toHaveAttribute("aria-pressed", "false");
  });

  it("troca os textos fixos da interface, o <html lang> e o título", async () => {
    const { user } = renderApp({ route: "/explore", language: "pt-BR" });
    expect(document.documentElement.lang).toBe("pt-BR");

    await user.click(languageGroup("Idioma").getByRole("button", { name: "English" }));

    expect(screen.getByRole("heading", { level: 1, name: "Explore projects" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Home" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Skip to main content" })).toBeInTheDocument();
    expect(screen.getByText("Nothing to show here yet.")).toBeInTheDocument(); // estado partilhado
    expect(screen.getByRole("contentinfo")).toHaveTextContent(
      "Project and organization content comes from external sources",
    );
    expect(document.documentElement.lang).toBe("en");
    expect(document.title).toBe("Explore · Kindred");
    expect(languageGroup("Language").getByRole("button", { name: "English" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("traduz também a página 404 e os estados partilhados", async () => {
    const { user } = renderApp({ route: "/nada", language: "pt-BR" });

    await user.click(languageGroup("Idioma").getByRole("button", { name: "English" }));

    expect(screen.getByRole("heading", { level: 1, name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to home" })).toBeInTheDocument();
  });

  it("volta ao português quando se escolhe Português", async () => {
    const { user } = renderApp({ language: "en" });

    await user.click(languageGroup("Language").getByRole("button", { name: "Português" }));

    expect(
      screen.getByRole("heading", { level: 1, name: "Bem-vindo à Kindred" }),
    ).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("pt-BR");
  });

  it("cada opção declara a sua própria língua (lang) para leitores de ecrã", () => {
    renderApp({ language: "pt-BR" });
    const group = languageGroup("Idioma");

    expect(group.getByRole("button", { name: "Português" })).toHaveAttribute("lang", "pt-BR");
    expect(group.getByRole("button", { name: "English" })).toHaveAttribute("lang", "en");
  });
});

describe("persistência do idioma", () => {
  it("guarda a escolha no localStorage", async () => {
    const { user } = renderApp({ language: "pt-BR" });

    await user.click(languageGroup("Idioma").getByRole("button", { name: "English" }));

    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe("en");
  });

  it("mantém o idioma ao navegar entre páginas", async () => {
    const { user } = renderApp({ language: "pt-BR" });

    await user.click(languageGroup("Idioma").getByRole("button", { name: "English" }));
    await user.click(
      within(screen.getByRole("navigation", { name: "Main navigation" })).getByRole("link", {
        name: "Explore",
      }),
    );

    expect(screen.getByRole("heading", { level: 1, name: "Explore projects" })).toBeInTheDocument();
    expect(languageGroup("Language").getByRole("button", { name: "English" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("mantém o idioma depois de recarregar a página", async () => {
    const first = renderApp({ language: "pt-BR" });
    await first.user.click(languageGroup("Idioma").getByRole("button", { name: "English" }));
    first.unmount();

    // "Recarregar": nova instância de i18n, sem idioma forçado, a ler o localStorage.
    renderApp();

    expect(
      screen.getByRole("heading", { level: 1, name: "Welcome to Kindred" }),
    ).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("en");
  });

  it("a preferência guardada tem prioridade sobre o idioma do browser", () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "en");
    mockBrowserLanguage("pt-BR");

    renderApp();

    expect(
      screen.getByRole("heading", { level: 1, name: "Welcome to Kindred" }),
    ).toBeInTheDocument();
  });

  it("sem preferência guardada, segue o idioma do browser (pt → pt-BR)", () => {
    mockBrowserLanguage("pt-PT");

    renderApp();

    expect(
      screen.getByRole("heading", { level: 1, name: "Bem-vindo à Kindred" }),
    ).toBeInTheDocument();
  });

  it("sem preferência e com browser noutra língua, usa inglês", () => {
    mockBrowserLanguage("fr-FR");

    renderApp();

    expect(
      screen.getByRole("heading", { level: 1, name: "Welcome to Kindred" }),
    ).toBeInTheDocument();
  });

  it("ignora um valor inválido guardado", () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "klingon");
    mockBrowserLanguage("pt-BR");

    renderApp();

    expect(
      screen.getByRole("heading", { level: 1, name: "Bem-vindo à Kindred" }),
    ).toBeInTheDocument();
  });

  it("continua a funcionar se o localStorage estiver indisponível", async () => {
    const denied = () => {
      throw new DOMException("denied", "SecurityError");
    };
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(denied);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(denied);
    mockBrowserLanguage("pt-BR");

    const { user } = renderApp();
    await user.click(languageGroup("Idioma").getByRole("button", { name: "English" }));

    expect(
      screen.getByRole("heading", { level: 1, name: "Welcome to Kindred" }),
    ).toBeInTheDocument();
  });
});
