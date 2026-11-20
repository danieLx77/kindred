import { useEffect, useRef, useState, type SubmitEvent } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";

import { DiscoveryError, fetchProjects } from "../api/discovery";
import { ProjectResultCard } from "../components/ProjectResultCard";
import { StateMessage } from "../components/StateMessage";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { paths } from "../routes";
import "./explore.css";

type Cursor = string | null;
type Result =
  | { status: "loading" }
  | { status: "error"; invalidCursor: boolean }
  | { status: "loaded"; data: Awaited<ReturnType<typeof fetchProjects>> };

function normalizeQuery(query: string) {
  return query.trim().replace(/\s+/g, " ");
}

function previousCursors(state: unknown): Cursor[] {
  if (!state || typeof state !== "object" || !("previousCursors" in state)) return [];
  const cursors: unknown = state.previousCursors;
  if (!Array.isArray(cursors)) return [];
  return cursors.every((cursor) => cursor === null || typeof cursor === "string") ? cursors : [];
}

interface ExploreResultsProps {
  query: string;
  cursor: Cursor;
  previous: Cursor[];
  focusResults: () => void;
  openPage: (query: string, cursor: Cursor, previous: Cursor[]) => void;
}

function ExploreResults({ query, cursor, previous, focusResults, openPage }: ExploreResultsProps) {
  const { t } = useTranslation();
  const [result, setResult] = useState<Result>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    void fetchProjects(query, cursor, controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setResult({ status: "loaded", data });
      },
      (error: unknown) => {
        if (!controller.signal.aborted) {
          setResult({
            status: "error",
            invalidCursor: error instanceof DiscoveryError && error.code === "invalid_cursor",
          });
        }
      },
    );
    return () => controller.abort();
  }, [query, cursor, attempt]);

  function retry() {
    focusResults();
    setResult({ status: "loading" });
    setAttempt((current) => current + 1);
  }

  const data = result.status === "loaded" ? result.data : null;
  const next = data?.pagination.next_cursor ?? null;
  const hasPrevious = cursor !== null && previous.length > 0;
  const showFirst =
    cursor !== null && (!hasPrevious || (result.status === "error" && result.invalidCursor));

  return (
    <>
      {result.status === "loading" && (
        <StateMessage variant="loading">{t("explore.loading")}</StateMessage>
      )}
      {result.status === "error" && (
        <StateMessage variant="error" onRetry={result.invalidCursor ? undefined : retry}>
          {t(result.invalidCursor ? "explore.invalidCursor" : "explore.error")}
        </StateMessage>
      )}
      {data && data.items.length === 0 && (
        <StateMessage variant="empty">
          {t(cursor !== null ? "explore.end" : query ? "explore.noMatches" : "explore.empty")}
        </StateMessage>
      )}
      {data && data.items.length > 0 && (
        <ul className="explore-results" aria-labelledby="explore-results-heading" role="list">
          {data.items.map((project) => (
            <li key={project.id}>
              <ProjectResultCard project={project} />
            </li>
          ))}
        </ul>
      )}
      <nav className="explore-pagination" aria-label={t("explore.paginationLabel")}>
        <button
          type="button"
          className="button button--secondary"
          disabled={!hasPrevious || result.status === "loading"}
          onClick={() => openPage(query, previous.at(-1) ?? null, previous.slice(0, -1))}
        >
          {t("explore.previous")}
        </button>
        <span role="status">{data ? t("explore.page", { page: data.pagination.page }) : ""}</span>
        <button
          type="button"
          className="button button--secondary"
          disabled={next === null}
          onClick={() => {
            if (next !== null) openPage(query, next, [...previous, cursor]);
          }}
        >
          {t("explore.next")}
        </button>
        {showFirst && (
          <button
            type="button"
            className="button button--secondary"
            onClick={() => openPage(query, null, [])}
          >
            {t("explore.first")}
          </button>
        )}
      </nav>
    </>
  );
}

export function ExplorePage() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const resultsHeading = useRef<HTMLHeadingElement>(null);
  const params = new URLSearchParams(location.search);
  const query = normalizeQuery(params.get("q") ?? "");
  const cursor = params.get("cursor") || null;
  const previous = previousCursors(location.state);
  const pageKey = JSON.stringify([query, cursor]);
  useDocumentTitle(t("explore.title"));

  function focusResults() {
    resultsHeading.current?.focus();
  }

  function openPage(nextQuery: string, nextCursor: Cursor, history: Cursor[]) {
    const search = new URLSearchParams();
    if (nextQuery) search.set("q", nextQuery);
    if (nextCursor !== null) search.set("cursor", nextCursor);
    if (search.toString() !== params.toString()) {
      void navigate(
        { pathname: paths.explore, search: search.toString() },
        {
          state: { previousCursors: history },
        },
      );
    }
    focusResults();
  }

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    const newQuery = normalizeQuery(String(new FormData(event.currentTarget).get("q") ?? ""));
    const input = event.currentTarget.querySelector("input");
    if (input) input.value = newQuery;
    openPage(newQuery, null, []);
  }

  return (
    <section className="explore" aria-labelledby="explore-heading">
      <div className="explore-intro">
        <h1 id="explore-heading">{t("explore.heading")}</h1>
        <p className="lead">{t("explore.lead")}</p>
        <form key={pageKey} role="search" onSubmit={submit}>
          <label htmlFor="explore-query">{t("explore.searchLabel")}</label>
          <div className="explore-search">
            <input id="explore-query" name="q" type="search" defaultValue={query} maxLength={200} />
            <button type="submit" className="button">
              {t("explore.search")}
            </button>
            <button
              type="reset"
              className="button button--secondary"
              onClick={() => openPage("", null, [])}
            >
              {t("explore.clear")}
            </button>
          </div>
        </form>
      </div>
      <section className="explore-section" aria-labelledby="explore-results-heading">
        <h2 id="explore-results-heading" ref={resultsHeading} tabIndex={-1}>
          {t("explore.results")}
        </h2>
        <ExploreResults
          key={pageKey}
          query={query}
          cursor={cursor}
          previous={previous}
          focusResults={focusResults}
          openPage={openPage}
        />
      </section>
    </section>
  );
}
