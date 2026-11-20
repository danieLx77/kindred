import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

import type { ProjectCard } from "../api/discovery";
import { paths } from "../routes";

function imageSource(value: string | null | undefined) {
  if (!value) return undefined;
  try {
    const url = new URL(value);
    if ((url.protocol === "https:" || url.protocol === "http:") && !url.username && !url.password) {
      return url.href;
    }
  } catch {
    return undefined;
  }
}

export function ProjectResultCard({ project }: { project: ProjectCard }) {
  const { t } = useTranslation();
  const [failedSource, setFailedSource] = useState<string>();
  const image = imageSource(project.image_url);
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
          <Link to={paths.project(project.id)}>
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
