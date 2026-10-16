import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { paths } from "../routes";

export function ProjectDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  useDocumentTitle(t("project.title"));

  return (
    <section className="page" aria-labelledby="project-heading">
      <h1 id="project-heading">{t("project.heading")}</h1>
      <p className="card">{t("project.identifier", { id })}</p>
      <Link className="button button--secondary" to={paths.explore}>
        {t("project.back")}
      </Link>
    </section>
  );
}
