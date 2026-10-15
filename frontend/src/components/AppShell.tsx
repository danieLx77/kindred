import { useEffect, useRef, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { paths } from "../routes";
import { BrandMark } from "./BrandMark";
import { LanguageSwitcher } from "./LanguageSwitcher";

const MAIN_ID = "main-content";
const CURRENT_YEAR = new Date().getFullYear();

export function AppShell() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const mainRef = useRef<HTMLElement>(null);
  const previousPathname = useRef(pathname);

  useEffect(() => {
    if (previousPathname.current !== pathname) {
      previousPathname.current = pathname;
      mainRef.current?.focus();
    }
  }, [pathname]);

  function handleSkipLink(event: MouseEvent<HTMLAnchorElement>) {
    event.preventDefault();
    mainRef.current?.focus();
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href={`#${MAIN_ID}`} onClick={handleSkipLink}>
        {t("a11y.skipToContent")}
      </a>

      <header className="app-header">
        <div className="app-header__inner">
          <NavLink to={paths.home} className="brand" end>
            <BrandMark />
            <span>{t("app.name")}</span>
          </NavLink>

          <nav className="main-nav" aria-label={t("a11y.mainNavigation")}>
            <ul>
              <li>
                <NavLink to={paths.home} end>
                  {t("nav.home")}
                </NavLink>
              </li>
              <li>
                <NavLink to={paths.explore}>{t("nav.explore")}</NavLink>
              </li>
            </ul>
          </nav>

          <LanguageSwitcher />
        </div>
      </header>

      <main id={MAIN_ID} ref={mainRef} tabIndex={-1} className="app-main">
        <Outlet />
      </main>

      <footer className="app-footer">
        <div className="app-footer__inner">
          <p>{t("footer.copyright", { year: CURRENT_YEAR })}</p>
          <p>{t("footer.externalContent")}</p>
        </div>
      </footer>
    </div>
  );
}
