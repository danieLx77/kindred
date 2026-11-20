import { screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import brazilFlag from "../assets/flags/br.svg";
import unitedStatesFlag from "../assets/flags/us.svg";
import { LANGUAGE_STORAGE_KEY } from "../i18n";
import { renderApp } from "../test/renderApp";

function languageGroup(name: "Idioma" | "Language") {
  return within(screen.getByRole("group", { name }));
}

function mockBrowserLanguage(language: string) {
  vi.spyOn(window.navigator, "language", "get").mockReturnValue(language);
}

describe("seletor de idioma", () => {
  it("exibe apenas as duas bandeiras SVG e marca o idioma ativo", () => {
    renderApp({ language: "pt-BR" });
    const group = languageGroup("Idioma");

    const portuguese = group.getByRole("button", { name: "Português (Brasil)" });
    const english = group.getByRole("button", { name: "Inglês (Estados Unidos)" });
    expect(portuguese).toHaveAttribute("aria-pressed", "true");
    expect(english).toHaveAttribute("aria-pressed", "false");

    expect(group.getAllByRole("button")).toHaveLength(2);
    expect(group.queryByRole("img")).not.toBeInTheDocument();
    for (const [button, flag] of [
      [portuguese, brazilFlag],
      [english, unitedStatesFlag],
    ] as const) {
      expect(button.textContent).toBe("");
      expect(button.querySelector("img")).toHaveAttribute("alt", "");
      expect(button.querySelector("img")).toHaveAttribute("src", flag);
    }
  });

  it("troca os textos fixos da interface, o <html lang> e o título", async () => {
    const { user } = renderApp({ route: "/explore", language: "pt-BR" });
    expect(document.documentElement.lang).toBe("pt-BR");

    await user.click(
      languageGroup("Idioma").getByRole("button", { name: "Inglês (Estados Unidos)" }),
    );

    expect(screen.getByRole("heading", { level: 1, name: "Explore projects" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Home" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Skip to main content" })).toBeInTheDocument();
    expect(await screen.findByText("No projects are available right now.")).toBeInTheDocument(); // estado partilhado
    expect(screen.getByRole("contentinfo")).toHaveTextContent(
      "Project and organization content comes from external sources",
    );
    expect(document.documentElement.lang).toBe("en");
    expect(document.title).toBe("Explore · Kindred");
    expect(
      languageGroup("Language").getByRole("button", { name: "English (United States)" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("traduz também a página 404 e os estados partilhados", async () => {
    const { user } = renderApp({ route: "/nada", language: "pt-BR" });

    await user.click(
      languageGroup("Idioma").getByRole("button", { name: "Inglês (Estados Unidos)" }),
    );

    expect(screen.getByRole("heading", { level: 1, name: "Page not found" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to home" })).toBeInTheDocument();
  });

  it("volta ao português quando se escolhe Português", async () => {
    const { user } = renderApp({ language: "en" });

    await user.click(
      languageGroup("Language").getByRole("button", { name: "Portuguese (Brazil)" }),
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Descubra projetos de impacto social" }),
    ).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("pt-BR");
    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe("pt-BR");
  });

  it("localiza os nomes acessíveis das duas opções no idioma da interface", async () => {
    const { user } = renderApp({ language: "pt-BR" });
    expect(
      languageGroup("Idioma").getByRole("button", { name: "Português (Brasil)" }),
    ).toBeInTheDocument();
    await user.click(
      languageGroup("Idioma").getByRole("button", { name: "Inglês (Estados Unidos)" }),
    );

    const group = languageGroup("Language");
    expect(group.getByRole("button", { name: "Portuguese (Brazil)" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
    expect(group.getByRole("button", { name: "English (United States)" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});

describe("persistência do idioma", () => {
  it("guarda a escolha no localStorage", async () => {
    const { user } = renderApp({ language: "pt-BR" });

    await user.click(
      languageGroup("Idioma").getByRole("button", { name: "Inglês (Estados Unidos)" }),
    );

    expect(window.localStorage.getItem(LANGUAGE_STORAGE_KEY)).toBe("en");
  });

  it("mantém o idioma ao navegar entre páginas", async () => {
    const { user } = renderApp({ language: "pt-BR" });

    await user.click(
      languageGroup("Idioma").getByRole("button", { name: "Inglês (Estados Unidos)" }),
    );
    await user.click(
      within(screen.getByRole("navigation", { name: "Main navigation" })).getByRole("link", {
        name: "Explore",
      }),
    );

    expect(screen.getByRole("heading", { level: 1, name: "Explore projects" })).toBeInTheDocument();
    expect(
      languageGroup("Language").getByRole("button", { name: "English (United States)" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("mantém o idioma depois de recarregar a página", async () => {
    const first = renderApp({ language: "pt-BR" });
    await first.user.click(
      languageGroup("Idioma").getByRole("button", { name: "Inglês (Estados Unidos)" }),
    );
    first.unmount();

    // "Recarregar": nova instância de i18n, sem idioma forçado, a ler o localStorage.
    renderApp();

    expect(
      screen.getByRole("heading", { level: 1, name: "Discover social impact projects" }),
    ).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("en");
  });

  it("a preferência guardada tem prioridade sobre o idioma do browser", () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "en");
    mockBrowserLanguage("pt-BR");

    renderApp();

    expect(
      screen.getByRole("heading", { level: 1, name: "Discover social impact projects" }),
    ).toBeInTheDocument();
  });

  it("sem preferência guardada, segue o idioma do browser (pt → pt-BR)", () => {
    mockBrowserLanguage("pt-PT");

    renderApp();

    expect(
      screen.getByRole("heading", { level: 1, name: "Descubra projetos de impacto social" }),
    ).toBeInTheDocument();
  });

  it("sem preferência e com browser noutra língua, usa inglês", () => {
    mockBrowserLanguage("fr-FR");

    renderApp();

    expect(
      screen.getByRole("heading", { level: 1, name: "Discover social impact projects" }),
    ).toBeInTheDocument();
  });

  it("ignora um valor inválido guardado", () => {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, "klingon");
    mockBrowserLanguage("pt-BR");

    renderApp();

    expect(
      screen.getByRole("heading", { level: 1, name: "Descubra projetos de impacto social" }),
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
    await user.click(
      languageGroup("Idioma").getByRole("button", { name: "Inglês (Estados Unidos)" }),
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Discover social impact projects" }),
    ).toBeInTheDocument();
  });
});
