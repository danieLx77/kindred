import type { SubmitEvent } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { BrandMark } from "../components/BrandMark";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { paths } from "../routes";

const QUERY_PARAMETER = "q";

export function HomePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  useDocumentTitle(t("home.title"));

  function handleSearch(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const input = new FormData(event.currentTarget).get(QUERY_PARAMETER);
    const query = String(input ?? "")
      .trim()
      .replace(/\s+/g, " ");
    const search = query ? new URLSearchParams({ [QUERY_PARAMETER]: query }).toString() : "";

    void navigate({ pathname: paths.explore, search });
  }

  return (
    <>
      <section className="hero" aria-labelledby="home-heading">
        <div className="hero__content">
          <h1 id="home-heading">{t("home.heading")}</h1>
          <p className="lead">{t("home.lead")}</p>
          <Link className="button" to={paths.explore}>
            {t("home.cta")}
          </Link>

          <form
            className="home-search"
            role="search"
            aria-labelledby="home-search-label"
            action={paths.explore}
            onSubmit={handleSearch}
          >
            <label id="home-search-label" htmlFor="home-search-input">
              {t("home.searchLabel")}
            </label>
            <div className="home-search__controls">
              <input id="home-search-input" name={QUERY_PARAMETER} type="search" />
              <button className="button button--secondary" type="submit">
                {t("home.searchSubmit")}
              </button>
            </div>
          </form>
        </div>
        <div className="hero__art" aria-hidden="true">
          <BrandMark />
        </div>
      </section>

      <section className="home-guide" aria-labelledby="home-guide-heading">
        <h2 id="home-guide-heading">{t("home.guideHeading")}</h2>
        <p>{t("home.guideDescription")}</p>
      </section>
    </>
  );
}
