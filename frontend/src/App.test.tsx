import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { renderApp } from "./test/renderApp";

describe("App", () => {
  it('mostra a Home em "/" e não o ecrã inicial do Vite', () => {
    renderApp({ language: "pt-BR" });

    expect(
      screen.getByRole("heading", { level: 1, name: "Bem-vindo à Kindred" }),
    ).toBeInTheDocument();

    expect(screen.queryByText(/vite \+ react/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /count is/i })).not.toBeInTheDocument();
  });

  it("expõe os pontos de referência semânticos (header, nav, main, footer)", () => {
    renderApp({ language: "pt-BR" });

    expect(screen.getByRole("banner")).toBeInTheDocument(); // <header>
    expect(screen.getByRole("navigation", { name: "Navegação principal" })).toBeInTheDocument(); // <nav>
    expect(screen.getByRole("main")).toBeInTheDocument(); // <main>
    expect(screen.getByRole("contentinfo")).toBeInTheDocument(); // <footer>
  });

  it("mantém o shell (navegação e rodapé) em todas as rotas", () => {
    renderApp({ route: "/explore", language: "en" });

    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Explore projects" })).toBeInTheDocument();
  });
});
