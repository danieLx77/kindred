import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

import type { ProjectCard } from "../api/projects";
import { paths } from "../routes";
import { safeExternalUrl } from "../safeExternalUrl";

export function ProjectResultCard({ project }: { project: ProjectCard }) {
  const { t } = useTranslation();
  const { search, state } = useLocation();
  const [failedSource, setFailedSource] = useState<string>();
  const image = safeExternalUrl(project.image_url);
  const metadata = [project.theme, project.country].filter(Boolean).join(" · ");

  return (
    <article className="explore-card">
      <div className="explore-card__media" aria-hidden="true">
        {image && image !== failedSource ? (
          <img
            src={image}
            alt=""
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setFailedSource(image)}
          />
        ) : null}
      </div>
      <div className="explore-card__content">
        <h3>
          <Link to={paths.project(project.id)} state={{ explore: { search, state } }}>
            {project.title || t("explore.untitledProject", { id: project.id })}
          </Link>
        </h3>
        {metadata && <p className="explore-card__meta">{metadata}</p>}
        {project.summary && <p>{project.summary}</p>}
        {project.organization?.name && (
          <p className="explore-card__meta">{project.organization.name}</p>
        )}
      </div>
    </article>
  );
}
