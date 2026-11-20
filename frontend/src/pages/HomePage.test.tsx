import { screen, within } from "@testing-library/react";
import { useLocation } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import App from "../App";
import { renderApp, renderWithProviders } from "../test/renderApp";

function LocationProbe() {
  const { pathname, search } = useLocation();
  return <output aria-label="Current location">{pathname + search}</output>;
}

function renderWithLocation(language: "pt-BR" | "en") {
  return renderWithProviders(
    <>
      <App />
      <LocationProbe />
    </>,
    { language },
  );
}

function currentLocation() {
  return screen.getByRole("status", { name: "Current location" }).textContent;
}

describe("Home", () => {
  it("apresenta o Kindred e a origem dos dados sem consultar a rede", () => {
    const fetch = vi.spyOn(window, "fetch");
    const xhr = vi.spyOn(window.XMLHttpRequest.prototype, "send");
    renderApp({ language: "pt-BR" });

    expect(screen.getByRole("banner")).toHaveTextContent("Kindred");
    const main = within(screen.getByRole("main"));
    expect(main.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Descubra projetos de impacto social",
    );
    expect(main.getByText(/encontrar iniciativas sociais/i)).toBeInTheDocument();
    expect(main.getByRole("heading", { level: 2 })).toHaveTextContent("página oficial");
    expect(main.getByRole("link", { name: "Explorar projetos" })).toHaveAttribute(
      "href",
      "/explore",
    );
    expect(
      within(screen.getByRole("contentinfo")).getByRole("link", { name: "GlobalGiving" }),
    ).toHaveAttribute("href", "https://www.globalgiving.org/");
    expect(fetch).not.toHaveBeenCalled();
    expect(xhr).not.toHaveBeenCalled();
  });

  it("envia com Enter, normaliza espaços e codifica caracteres especiais", async () => {
    const { user } = renderWithLocation("pt-BR");
    const form = screen.getByRole("search", { name: "Pesquisar projetos sociais" });
    const field = within(form).getByRole("searchbox", { name: "Pesquisar projetos sociais" });

    await user.type(field, "  educação   &   inclusão + saúde? #ação  {Enter}");

    expect(currentLocation()).toBe(
      "/explore?q=educa%C3%A7%C3%A3o+%26+inclus%C3%A3o+%2B+sa%C3%BAde%3F+%23a%C3%A7%C3%A3o",
    );
    expect(
      screen.getByRole("heading", { level: 1, name: "Explorar projetos" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveFocus();
  });

  it("traduz a Home, mantém o termo durante a troca de idioma e envia pelo botão", async () => {
    const { user, unmount } = renderWithLocation("pt-BR");
    await user.type(screen.getByRole("searchbox", { name: "Pesquisar projetos sociais" }), "water");
    await user.click(screen.getByRole("button", { name: "Inglês (Estados Unidos)" }));

    expect(
      screen.getByRole("heading", { level: 1, name: "Discover social impact projects" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/learn about the work they do/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("official project page");
    expect(screen.getByRole("link", { name: "Explore projects" })).toHaveAttribute(
      "href",
      "/explore",
    );
    expect(screen.getByRole("searchbox", { name: "Search social projects" })).toHaveValue("water");
    await user.click(screen.getByRole("button", { name: "Search" }));

    expect(currentLocation()).toBe("/explore?q=water");
    expect(screen.getByRole("heading", { level: 1, name: "Explore projects" })).toBeInTheDocument();

    unmount();
    renderApp();
    expect(screen.getByRole("searchbox", { name: "Search social projects" })).toBeInTheDocument();
  });

  it.each(["", "   "])("abre Explore sem parâmetro para o termo %j", async (query) => {
    const { user } = renderWithLocation("en");
    const field = screen.getByRole("searchbox", { name: "Search social projects" });
    if (query) await user.type(field, query);
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(currentLocation()).toBe("/explore");
  });

  it("percorre ação principal, campo e botão com Tab e ativa Explore com Enter", async () => {
    const { user } = renderWithLocation("en");
    screen.getByRole("button", { name: "English (United States)" }).focus();

    const explore = screen.getByRole("link", { name: "Explore projects" });
    const field = screen.getByRole("searchbox", { name: "Search social projects" });
    const submit = screen.getByRole("button", { name: "Search" });

    for (const control of [explore, field, submit]) {
      await user.tab();
      expect(control).toHaveFocus();
    }

    await user.tab({ shift: true });
    expect(field).toHaveFocus();
    await user.tab({ shift: true });
    expect(explore).toHaveFocus();

    await user.keyboard("{Enter}");
    expect(currentLocation()).toBe("/explore");
  });
});
