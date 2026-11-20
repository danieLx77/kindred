import { fireEvent, screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw/http";
import { useLocation, useNavigate } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "../App";
import { discoveryPath } from "../api/projects";
import { server } from "../test/msw/server";
import { renderApp, renderWithProviders } from "../test/renderApp";

const endpoint = new URL(discoveryPath, window.location.href).href;
const official = "https://www.globalgiving.org/projects/learning-for-all/";
const full = {
  id: "42",
  title: "Learning for all",
  summary: "Community classrooms",
  theme: "Education",
  country: "Brazil",
  region: "Minas Gerais",
  organization: { id: "2", name: "Open School" },
  image_url: "https://example.test/project.jpg",
  activities: "Train local teachers",
  need: "Bring schools closer",
  long_term_impact: "More students graduate",
  official_url: official,
};

function deferred() {
  let release!: () => void;
  const promise = new Promise<void>((resolve) => {
    release = resolve;
  });
  return { promise, release };
}

function LocationProbe() {
  const { pathname, search } = useLocation();
  const navigate = useNavigate();
  return (
    <>
      <output aria-label="Location">{pathname + search}</output>
      <button type="button" onClick={() => void navigate("/projects/43")}>
        Next project
      </button>
    </>
  );
}

function renderJourney(route: string) {
  return renderWithProviders(
    <>
      <App />
      <LocationProbe />
    </>,
    { route, language: "pt-BR" },
  );
}

describe("Project Detail", () => {
  it("mostra os dados completos, distingue o link externo e troca o idioma sem nova chamada", async () => {
    const requests: string[] = [];
    const gate = deferred();
    server.use(
      http.get(`${endpoint}/42`, async ({ request }) => {
        requests.push(request.url);
        await gate.promise;
        return HttpResponse.json(full);
      }),
    );
    const { user } = renderApp({ route: "/projects/00042", language: "pt-BR" });
    expect(screen.getByRole("status")).toHaveTextContent("Carregando detalhes do projeto…");
    gate.release();
    const title = await screen.findByRole("heading", { name: full.title, level: 1 });
    expect(title).toBeInTheDocument();
    expect(document.title).toBe("Learning for all · Kindred");
    for (const text of [
      full.summary,
      full.theme,
      "Minas Gerais, Brazil",
      full.organization.name,
      full.activities,
      full.need,
      full.long_term_impact,
    ]) {
      expect(screen.getByText(text)).toBeInTheDocument();
    }
    expect(screen.getByRole("heading", { name: "Atividades", level: 2 })).toBeInTheDocument();
    const main = screen.getByRole("main");
    const image = main.querySelector("img");
    expect(image).toHaveAttribute("src", full.image_url);
    expect(image).toHaveAttribute("alt", "");
    expect(image).toHaveAttribute("referrerpolicy", "no-referrer");
    fireEvent.error(image!);
    expect(main.querySelector("img")).toBeNull();
    const action = screen.getByRole("link", { name: /página oficial.*site externo/i });
    expect(action).toHaveAttribute("href", official);
    expect(action).toHaveAttribute("referrerpolicy", "no-referrer");
    expect(action).not.toHaveAttribute("target");
    screen.getByRole("link", { name: "Voltar para Explorar" }).focus();
    await user.tab();
    expect(action).toHaveFocus();

    await user.click(screen.getByRole("button", { name: "English" }));
    expect(screen.getByRole("heading", { name: "Long-term impact", level: 2 })).toBeInTheDocument();
    expect(screen.getByText(full.long_term_impact)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /official project page.*external site/i }),
    ).toHaveAttribute("href", official);
    expect(requests).toEqual([`${endpoint}/42`]);
  });

  it("aceita dados parciais e retorna ao catálogo no acesso direto", async () => {
    server.use(
      http.get(`${endpoint}/42`, () =>
        HttpResponse.json({
          id: "42",
          title: null,
          summary: null,
          country: "Brazil",
          region: null,
          organization: null,
          official_url: null,
          image_url: null,
          activities: null,
        }),
      ),
    );
    const { user } = renderJourney("/projects/42");
    expect(await screen.findByText("Brazil")).toBeInTheDocument();
    const main = within(screen.getByRole("main"));
    expect(main.getByRole("heading", { level: 1 })).toHaveTextContent("Detalhes do projeto");
    expect(main.queryByRole("heading", { level: 2 })).not.toBeInTheDocument();
    expect(main.queryByText("Organização")).not.toBeInTheDocument();
    expect(main.queryByRole("link", { name: /site externo/i })).not.toBeInTheDocument();
    expect(screen.getByRole("main").querySelector("img")).toBeNull();
    await user.click(main.getByRole("link", { name: "Voltar para Explorar" }));
    expect(screen.getByLabelText("Location")).toHaveTextContent("/explore");
  });

  it.each([
    "javascript:alert(1)",
    "https://user:pass@example.test/project",
    "https://example.test/project?%61pi_key=secret",
    "//example.test/project",
  ])("omite um link externo inválido", async (url) => {
    server.use(http.get(`${endpoint}/42`, () => HttpResponse.json({ ...full, official_url: url })));
    renderApp({ route: "/projects/42", language: "pt-BR" });
    await screen.findByRole("heading", { name: full.title });
    expect(screen.queryByRole("link", { name: /site externo/i })).not.toBeInTheDocument();
  });

  it("rejeita identificadores locais inválidos antes da rede", () => {
    let calls = 0;
    server.use(
      http.get(`${endpoint}/:id`, () => {
        calls++;
        return HttpResponse.json(full);
      }),
    );
    renderApp({ route: "/projects/0", language: "en" });
    expect(screen.getByRole("status")).toHaveTextContent("This project identifier is invalid.");
    expect(screen.getByRole("link", { name: "Back to Explore" })).toBeInTheDocument();
    expect(calls).toBe(0);
  });

  it.each([
    [404, "project_not_found", "Projeto não encontrado."],
    [422, "invalid_request", "O identificador deste projeto é inválido."],
  ])("distingue status %s de indisponibilidade", async (status, code, message) => {
    server.use(http.get(`${endpoint}/42`, () => HttpResponse.json({ code }, { status })));
    renderApp({ route: "/projects/42", language: "pt-BR" });
    expect(await screen.findByText(message)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Tentar novamente" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Voltar para Explorar" })).toBeInTheDocument();
  });

  it.each(["timeout", "5xx", "network", "mismatch"])(
    "permite repetir após falha %s",
    async (failure) => {
      let attempts = 0;
      server.use(
        http.get(`${endpoint}/42`, () => {
          if (++attempts > 1) return HttpResponse.json(full);
          if (failure === "network") return HttpResponse.error();
          if (failure === "mismatch") return HttpResponse.json({ ...full, id: "43" });
          return HttpResponse.json(
            { code: "internal-provider-data" },
            { status: failure === "timeout" ? 504 : 503 },
          );
        }),
      );
      const { user } = renderApp({ route: "/projects/42", language: "pt-BR" });
      const alert = await screen.findByRole("alert");
      expect(alert).toHaveTextContent("Não foi possível carregar os detalhes");
      expect(alert).not.toHaveTextContent("internal-provider-data");
      await user.click(within(alert).getByRole("button", { name: "Tentar novamente" }));
      expect(await screen.findByRole("heading", { name: full.title })).toHaveFocus();
      expect(attempts).toBe(2);
    },
  );

  it("cancela a requisição do ID anterior", async () => {
    const requested = deferred();
    const gate = deferred();
    let signal: AbortSignal | undefined;
    server.use(
      http.get(`${endpoint}/42`, async ({ request }) => {
        signal = request.signal;
        requested.release();
        await gate.promise;
        return HttpResponse.json(full);
      }),
      http.get(`${endpoint}/43`, () => HttpResponse.json({ id: "43", title: "Second project" })),
    );
    const { user } = renderJourney("/projects/42");
    await requested.promise;
    await user.click(screen.getByRole("button", { name: "Next project" }));
    expect(await screen.findByRole("heading", { name: "Second project" })).toBeInTheDocument();
    expect(signal?.aborted).toBe(true);
    gate.release();
    expect(screen.queryByText(full.title)).not.toBeInTheDocument();
  });

  it("percorre Home → Explore → Detail → link oficial e preserva busca e página ao voltar", async () => {
    const visits: string[] = [];
    server.use(
      http.get(endpoint, ({ request }) => {
        const params = new URL(request.url).searchParams;
        const cursor = params.get("cursor");
        expect(params.get("q")).toBe("education");
        visits.push(cursor ?? "first");
        return HttpResponse.json({
          items: [cursor ? full : { id: "28", title: "Another project" }],
          pagination: {
            page: cursor ? 2 : 1,
            page_size: 10,
            next_cursor: cursor ? null : "opaque",
          },
        });
      }),
      http.get(`${endpoint}/42`, () => {
        visits.push("detail");
        return HttpResponse.json(full);
      }),
    );
    const { user } = renderJourney("/");
    await user.type(screen.getByRole("searchbox"), "education{Enter}");
    await screen.findByRole("link", { name: "Another project" });
    await user.click(screen.getByRole("button", { name: "Próxima" }));
    await user.click(await screen.findByRole("link", { name: full.title }));
    expect(screen.getByLabelText("Location")).toHaveTextContent("/projects/42");
    expect(await screen.findByRole("link", { name: /site externo/i })).toHaveAttribute(
      "href",
      official,
    );
    await user.click(screen.getByRole("link", { name: "Voltar para Explorar" }));
    await screen.findByText("Página 2");
    expect(screen.getByRole("searchbox")).toHaveValue("education");
    expect(screen.getByLabelText("Location")).toHaveTextContent(
      "/explore?q=education&cursor=opaque",
    );
    await user.click(screen.getByRole("button", { name: "Anterior" }));
    await screen.findByText("Página 1");
    expect(visits).toEqual(["first", "opaque", "detail", "opaque", "first"]);
  });
});
