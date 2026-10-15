import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders } from "../test/renderApp";
import { StateMessage } from "./StateMessage";

describe("StateMessage", () => {
  it.each([
    ["pt-BR", "loading", "Carregando…"],
    ["pt-BR", "error", "Algo deu errado. Tente novamente."],
    ["pt-BR", "empty", "Nada para mostrar por aqui ainda."],
    ["en", "loading", "Loading…"],
    ["en", "error", "Something went wrong. Please try again."],
    ["en", "empty", "Nothing to show here yet."],
  ] as const)("traduz o estado %s / %s", (language, variant, text) => {
    renderWithProviders(<StateMessage variant={variant} />, { language });

    expect(screen.getByText(text)).toBeInTheDocument();
  });

  it('anuncia erros com role="alert" e os outros estados com role="status"', () => {
    const { unmount } = renderWithProviders(<StateMessage variant="error" />, {
      language: "pt-BR",
    });
    expect(screen.getByRole("alert")).toBeInTheDocument();
    unmount();

    renderWithProviders(<StateMessage variant="loading" />, {
      language: "pt-BR",
    });
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it('mostra "Tentar novamente" só em erro e só se houver onRetry', async () => {
    const onRetry = vi.fn();
    const { user, unmount } = renderWithProviders(
      <StateMessage variant="error" onRetry={onRetry} />,
      { language: "pt-BR" },
    );

    await user.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
    unmount();

    renderWithProviders(<StateMessage variant="error" />, { language: "pt-BR" });
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("aceita um texto específico no lugar do padrão", () => {
    renderWithProviders(
      <StateMessage variant="empty">Sem resultados para esta busca.</StateMessage>,
      { language: "pt-BR" },
    );

    expect(screen.getByText("Sem resultados para esta busca.")).toBeInTheDocument();
    expect(screen.queryByText("Nada para mostrar por aqui ainda.")).not.toBeInTheDocument();
  });
});
