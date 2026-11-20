import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useParams } from "react-router-dom";

import { fetchProject, KindredApiError, type ProjectDetail } from "../api/projects";
import { StateMessage } from "../components/StateMessage";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { paths } from "../routes";
import { safeExternalUrl } from "../safeExternalUrl";
import "./project-detail.css";

type DetailResult =
  | { status: "loading" | "notFound" | "invalidId" | "error" }
  | { status: "loaded"; project: ProjectDetail };

function canonicalProjectId(id: string | undefined) {
  if (!id || id.length > 20 || /[^0-9]/.test(id)) return "";
  return id.replace(/^0+/, "");
}

function DetailContent({ project }: { project: ProjectDetail }) {
  const { t } = useTranslation();
  const [failedImage, setFailedImage] = useState<string>();
  const image = safeExternalUrl(project.image_url);
  const official = safeExternalUrl(project.official_url);
  const location = [project.region, project.country].filter(Boolean).join(", ");
  const sections = [
    { title: t("project.activities"), text: project.activities },
    { title: t("project.need"), text: project.need },
    { title: t("project.impact"), text: project.long_term_impact },
  ];

  return (
    <>
      <div className="project-detail__intro">
        {image && image !== failedImage && (
          <img
            className="project-detail__image"
            src={image}
            alt=""
            referrerPolicy="no-referrer"
            onError={() => setFailedImage(image)}
          />
        )}
        {project.summary && <p className="lead project-detail__summary">{project.summary}</p>}
        {(project.theme || location || project.organization) && (
          <dl className="project-detail__facts">
            {project.theme && (
              <div>
                <dt>{t("project.theme")}</dt>
                <dd>{project.theme}</dd>
              </div>
            )}
            {location && (
              <div>
                <dt>{t("project.location")}</dt>
                <dd>{location}</dd>
              </div>
            )}
            {project.organization && (
              <div>
                <dt>{t("project.organization")}</dt>
                <dd>
                  {project.organization.name ||
                    t("project.organizationReference", { id: project.organization.id })}
                </dd>
              </div>
            )}
          </dl>
        )}
        {official && (
          <a
            className="button project-detail__official"
            href={official}
            referrerPolicy="no-referrer"
          >
            {t("project.official")}
          </a>
        )}
      </div>
      {sections.map(({ title, text }) =>
        text ? (
          <section key={title} className="project-detail__section">
            <h2>{title}</h2>
            <p>{text}</p>
          </section>
        ) : null,
      )}
    </>
  );
}

function ProjectDetail({ id }: { id: string }) {
  const { t } = useTranslation();
  const heading = useRef<HTMLHeadingElement>(null);
  const [result, setResult] = useState<DetailResult>({ status: id ? "loading" : "invalidId" });
  const [attempt, setAttempt] = useState(0);
  const title = (result.status === "loaded" && result.project.title) || t("project.heading");

  useDocumentTitle(title);

  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();
    void fetchProject(id, controller.signal).then(
      (project) => {
        if (!controller.signal.aborted) setResult({ status: "loaded", project });
      },
      (error: unknown) => {
        if (controller.signal.aborted) return;
        const status = error instanceof KindredApiError ? error.status : 0;
        setResult({ status: status === 404 ? "notFound" : status === 422 ? "invalidId" : "error" });
      },
    );
    return () => controller.abort();
  }, [id, attempt]);

  function retry() {
    heading.current?.focus();
    setResult({ status: "loading" });
    setAttempt((current) => current + 1);
  }

  return (
    <>
      <h1 id="project-heading" ref={heading} tabIndex={-1}>
        {title}
      </h1>
      {result.status === "loaded" && <DetailContent project={result.project} />}
      {result.status === "loading" && (
        <StateMessage variant="loading">{t("project.loading")}</StateMessage>
      )}
      {result.status === "notFound" && (
        <StateMessage variant="empty">{t("project.notFound")}</StateMessage>
      )}
      {result.status === "invalidId" && (
        <StateMessage variant="empty">{t("project.invalidId")}</StateMessage>
      )}
      {result.status === "error" && (
        <StateMessage variant="error" onRetry={retry}>
          {t("project.error")}
        </StateMessage>
      )}
    </>
  );
}

export function ProjectDetailPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const { state } = useLocation();
  const previous = (state as { explore?: { search?: string; state?: unknown } } | null)?.explore;
  const search = typeof previous?.search === "string" ? previous.search : "";
  const canonicalId = canonicalProjectId(id);

  return (
    <section className="project-detail" aria-labelledby="project-heading">
      <Link
        className="project-detail__back"
        to={{ pathname: paths.explore, search }}
        state={previous?.state}
      >
        {t("project.back")}
      </Link>
      <ProjectDetail key={canonicalId} id={canonicalId} />
    </section>
  );
}
