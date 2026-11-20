import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { http, HttpResponse } from "msw/http";
import { useLocation, useNavigate } from "react-router-dom";
import { describe, expect, it } from "vitest";

import App from "../App";
import { discoveryPath, type ProjectCard } from "../api/projects";
import { server } from "../test/msw/server";
import { renderWithProviders } from "../test/renderApp";

const endpoint = new URL(discoveryPath, window.location.href).href;
const education = { id: "42", title: "Learning for all", theme: "Education", country: "Brazil" };

function response(items: ProjectCard[], page = 1, next_cursor: string | null = null) {
  return HttpResponse.json({ items, pagination: { page, page_size: 9, next_cursor } });
}

function LocationProbe() {
  const { pathname, search } = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <output aria-label="Location">{pathname + search}</output>
      <button type="button" onClick={() => void navigate(-1)}>
        History back
      </button>
    </>
  );
}

function renderExplore(route = "/explore", language: "pt-BR" | "en" = "pt-BR") {
  return renderWithProviders(
    <>
      <App />
      <LocationProbe />
    </>,
    { route, language },
  );
}

function location() {
  return screen.getByLabelText("Location").textContent;
}

function deferred() {
  let release!: () => void;
  const promise = new Promise<void>((resolve) => {
    release = resolve;
  });
  return { promise, release };
}

describe("Explore", () => {
  it("carrega o catálogo, mostra cards completos e parciais e abre a rota de detalhe", async () => {
    const gate = deferred();
    server.use(
      http.get(endpoint, async ({ request }) => {
        expect(new URL(request.url).search).toBe("?page_size=9");
        await gate.promise;
        return response([
          {
            ...education,
            summary: "Community classrooms.",
            organization: { id: "2", name: "Open School" },
            image_url: "https://example.test/card-large.jpg",
          },
          { id: "43", image_url: null, title: null, organization: null },
        ]);
      }),
    );
    const { user } = renderExplore();
    expect(screen.getByText("Carregando projetos…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Próxima" })).toBeDisabled();
    gate.release();

    const list = await screen.findByRole("list", { name: "Resultados de projetos" });
    expect(within(list).getAllByRole("listitem")).toHaveLength(2);
    expect(within(list).getByText("Education · Brazil")).toBeInTheDocument();
    expect(within(list).getByText("Open School")).toBeInTheDocument();
    expect(within(list).getByText("Community classrooms.")).toBeInTheDocument();
    const image = list.querySelector("img");
    expect(image).toHaveAttribute("src", "https://example.test/card-large.jpg");
    expect(image).toHaveAttribute("alt", "");
    expect(image).toHaveAttribute("loading", "lazy");
    expect(image).toHaveAttribute("referrerpolicy", "no-referrer");
    fireEvent.error(image!);
    expect(list.querySelector("img")).toBeNull();
    expect(list.querySelectorAll('.explore-card__media[aria-hidden="true"]')).toHaveLength(2);
    const partialLink = within(list).getByRole("link", { name: "Projeto 43" });
    expect(partialLink).toHaveAttribute("href", "/projects/43");
    await user.click(partialLink);
    expect(location()).toBe("/projects/43");
    expect(screen.getByRole("heading", { name: "Detalhes do projeto" })).toBeInTheDocument();
  });

  it("consome a consulta da Home, normaliza espaços e mantém caracteres especiais", async () => {
    const seen: string[] = [];
    server.use(
      http.get(endpoint, ({ request }) => {
        seen.push(new URL(request.url).searchParams.get("q") ?? "");
        return response([education]);
      }),
    );
    const { user } = renderExplore("/");
    await user.type(screen.getByRole("searchbox"), "  educação   & inclusão+ {Enter}");
    expect(await screen.findByRole("link", { name: education.title })).toBeInTheDocument();
    expect(screen.getByRole("searchbox", { name: "Pesquisar projetos sociais" })).toHaveValue(
      "educação & inclusão+",
    );
    expect(location()).toBe("/explore?q=educa%C3%A7%C3%A3o+%26+inclus%C3%A3o%2B");
    expect(seen).toEqual(["educação & inclusão+"]);
  });

  it("avança e volta pelos cursores públicos, inclusive após histórico do navegador", async () => {
    const seen: string[] = [];
    server.use(
      http.get(endpoint, ({ request }) => {
        const params = new URL(request.url).searchParams;
        expect(params.get("q")).toBe("educação");
        const cursor = params.get("cursor") ?? "";
        seen.push(cursor);
        if (cursor === "second+/=") return response([{ id: "2", title: "Second" }], 2, "third");
        if (cursor === "third") return response([], 3);
        return response([education], 1, "second+/=");
      }),
    );
    const { user } = renderExplore("/explore?q=educação");
    const next = () => screen.getByRole("button", { name: "Próxima" });
    const previous = () => screen.getByRole("button", { name: "Anterior" });
    await screen.findByText("Página 1");
    expect(previous()).toBeDisabled();

    next().focus();
    await user.keyboard("{Enter}");
    await screen.findByText("Página 2");
    expect(screen.getByRole("heading", { name: "Resultados de projetos" })).toHaveFocus();
    expect(location()).toBe("/explore?q=educa%C3%A7%C3%A3o&cursor=second%2B%2F%3D");
    await user.click(screen.getByRole("button", { name: "Inglês (Estados Unidos)" }));
    expect(screen.getByText("Page 2")).toBeInTheDocument();
    expect(screen.getByRole("searchbox", { name: "Search social projects" })).toHaveValue(
      "educação",
    );
    expect(screen.getByRole("link", { name: "Second" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeEnabled();
    expect(location()).toBe("/explore?q=educa%C3%A7%C3%A3o&cursor=second%2B%2F%3D");
    expect(seen).toEqual(["", "second+/="]);
    await user.click(screen.getByRole("button", { name: "Portuguese (Brazil)" }));
    expect(screen.getByText("Página 2")).toBeInTheDocument();
    await user.click(next());
    await screen.findByText("Página 3");
    expect(screen.getByText(/Não há mais resultados/)).toBeInTheDocument();
    expect(next()).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "History back" }));
    await screen.findByText("Página 2");
    await user.click(previous());
    await screen.findByText("Página 1");
    expect(previous()).toBeDisabled();
    expect(location()).toBe("/explore?q=educa%C3%A7%C3%A3o");
    expect(seen).toEqual(["", "second+/=", "third"]);
  });

  it.each(["", "água"])(
    "exibe todos os projetos na ordem em páginas de nove (%s)",
    async (query) => {
      const projects = Array.from({ length: 31 }, (_, index) => ({
        id: String(101 + index * 7),
        title: `Projeto ${index + 1}`,
      }));
      server.use(
        http.get(endpoint, ({ request }) => {
          const params = new URL(request.url).searchParams;
          expect(params.get("q") ?? "").toBe(query);
          expect(params.get("page_size")).toBe("9");
          const page = Number(params.get("cursor")?.replace("opaque-", "") ?? "1");
          return response(
            projects.slice((page - 1) * 9, page * 9),
            page,
            page < 4 ? `opaque-${page + 1}` : null,
          );
        }),
      );
      const { user } = renderExplore(
        query ? `/explore?q=${encodeURIComponent(query)}` : "/explore",
      );
      const next = () => screen.getByRole("button", { name: "Próxima" });
      const previous = () => screen.getByRole("button", { name: "Anterior" });

      async function expectPage(page: number) {
        await screen.findByText(`Página ${page}`);
        const list = screen.getByRole("list", { name: "Resultados de projetos" });
        expect(
          within(list)
            .getAllByRole("link")
            .map((link) => link.textContent),
        ).toEqual(projects.slice((page - 1) * 9, page * 9).map((project) => project.title));
      }

      await expectPage(1);
      for (const page of [2, 3, 4]) {
        await user.click(next());
        await expectPage(page);
      }
      expect(next()).toBeDisabled();
      for (const page of [3, 2, 1]) {
        await user.click(previous());
        await expectPage(page);
      }
      expect(previous()).toBeDisabled();
    },
  );

  it("exibe nove projetos quando a primeira página também é a última", async () => {
    const projects = Array.from({ length: 9 }, (_, index) => ({
      id: String(index + 1),
      title: `Projeto ${index + 1}`,
    }));
    server.use(http.get(endpoint, () => response(projects)));
    renderExplore("/explore");

    const list = await screen.findByRole("list", { name: "Resultados de projetos" });
    expect(within(list).getAllByRole("listitem")).toHaveLength(9);
    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Próxima" })).toBeDisabled();
  });

  it("reinicia a posição ao enviar outra consulta e volta ao catálogo ao limpar ou enviar vazio", async () => {
    const queries: string[] = [];
    server.use(
      http.get(endpoint, ({ request }) => {
        const params = new URL(request.url).searchParams;
        const query = params.get("q") ?? "";
        queries.push(query);
        if (query === "water")
          return response([], params.has("cursor") ? 2 : 1, params.has("cursor") ? null : "opaque");
        if (query) return response([]);
        return response([education]);
      }),
    );
    const { user } = renderExplore("/explore?q=water");
    await screen.findByText("Página 1");
    await user.click(screen.getByRole("button", { name: "Próxima" }));
    await screen.findByText("Página 2");
    const form = screen.getByRole("search");
    await user.clear(within(form).getByRole("searchbox"));
    await user.type(within(form).getByRole("searchbox"), "  saúde   pública ");
    await user.click(within(form).getByRole("button", { name: "Pesquisar" }));
    await screen.findByText("Nenhum projeto corresponde à busca.");
    expect(location()).toBe("/explore?q=sa%C3%BAde+p%C3%BAblica");
    expect(screen.getByText("Página 1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "Limpar busca" }));
    await screen.findByRole("link", { name: education.title });
    expect(location()).toBe("/explore");
    expect(screen.getByRole("searchbox")).toHaveValue("");

    await user.type(screen.getByRole("searchbox"), "water{Enter}");
    await screen.findByText("Nenhum projeto corresponde à busca.");
    await user.clear(screen.getByRole("searchbox"));
    await user.type(screen.getByRole("searchbox"), "   {Enter}");
    await screen.findByRole("link", { name: education.title });
    expect(location()).toBe("/explore");
    expect(queries).toEqual(["water", "water", "saúde pública", ""]);
  });

  it.each(["http", "network", "invalid"])(
    "repete a mesma pesquisa após falha %s",
    async (failure) => {
      const requests: string[] = [];
      server.use(
        http.get(endpoint, ({ request }) => {
          requests.push(new URL(request.url).search);
          if (requests.length > 1) return response([education]);
          if (failure === "network") return HttpResponse.error();
          if (failure === "invalid") return HttpResponse.json({ items: [] });
          return HttpResponse.json(
            { code: "provider_timeout", detail: "internal" },
            { status: 504 },
          );
        }),
      );
      const { user } = renderExplore("/explore?q=education&cursor=opaque");
      const alert = await screen.findByRole("alert");
      expect(alert).toHaveTextContent("Não foi possível carregar os projetos.");
      expect(alert).not.toHaveTextContent("internal");
      await user.click(within(alert).getByRole("button", { name: "Tentar novamente" }));
      await screen.findByRole("link", { name: education.title });
      expect(requests).toEqual([
        "?page_size=9&q=education&cursor=opaque",
        "?page_size=9&q=education&cursor=opaque",
      ]);
    },
  );

  it("reinicia uma navegação expirada sem perder a busca", async () => {
    server.use(
      http.get(endpoint, ({ request }) =>
        new URL(request.url).searchParams.has("cursor")
          ? HttpResponse.json({ code: "invalid_cursor" }, { status: 400 })
          : response([education]),
      ),
    );
    const { user } = renderExplore("/explore?q=education&cursor=expired", "en");
    expect(await screen.findByRole("alert")).toHaveTextContent("expired");
    await user.click(screen.getByRole("button", { name: "First page" }));
    await screen.findByRole("link", { name: education.title });
    expect(location()).toBe("/explore?q=education");
  });

  it("busca um novo cursor ao reiniciar a paginação depois de uma resposta de cursor inválido", async () => {
    const cursors: (string | null)[] = [];
    server.use(
      http.get(endpoint, ({ request }) => {
        const cursor = new URL(request.url).searchParams.get("cursor");
        cursors.push(cursor);
        if (cursor === "stale")
          return HttpResponse.json({ code: "invalid_cursor" }, { status: 400 });
        if (cursor === "new") return response([{ id: "2", title: "Second" }], 2);
        return response([education], 1, cursors.length === 1 ? "stale" : "new");
      }),
    );
    const { user } = renderExplore("/explore?q=water");
    await screen.findByRole("link", { name: education.title });
    await user.click(screen.getByRole("button", { name: "Próxima" }));
    await screen.findByRole("alert");
    await user.click(screen.getByRole("button", { name: "Primeira página" }));
    await screen.findByRole("link", { name: education.title });
    await user.click(screen.getByRole("button", { name: "Próxima" }));
    await screen.findByRole("link", { name: "Second" });
    expect(cursors).toEqual([null, "stale", null, "new"]);
  });

  it("cancela a busca obsoleta e preserva os resultados e consulta ao trocar de idioma", async () => {
    const requested = deferred();
    const slow = deferred();
    const returned = deferred();
    const queries: string[] = [];
    let oldSignal: AbortSignal | undefined;
    server.use(
      http.get(endpoint, async ({ request }) => {
        const query = new URL(request.url).searchParams.get("q") ?? "";
        queries.push(query);
        if (query === "slow") {
          oldSignal = request.signal;
          requested.release();
          await slow.promise;
          returned.release();
          return response([{ id: "7", title: "Obsolete project" }]);
        }
        return response([education]);
      }),
    );
    const { user } = renderExplore("/explore?q=slow");
    await requested.promise;
    await user.clear(screen.getByRole("searchbox"));
    await user.type(screen.getByRole("searchbox"), "fast{Enter}");
    await screen.findByRole("link", { name: education.title });
    expect(oldSignal?.aborted).toBe(true);
    slow.release();
    await returned.promise;

    await user.click(screen.getByRole("button", { name: "Inglês (Estados Unidos)" }));
    expect(screen.getByRole("searchbox", { name: "Search social projects" })).toHaveValue("fast");
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByRole("link", { name: education.title })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Obsolete project" })).not.toBeInTheDocument();
    await waitFor(() => expect(queries).toEqual(["slow", "fast"]));
  });
});
