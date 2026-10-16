import { useTranslation } from "react-i18next";
import { StateMessage } from "../components/StateMessage";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

export function ExplorePage() {
  const { t } = useTranslation();
  useDocumentTitle(t("explore.title"));

  return (
    <section className="page" aria-labelledby="explore-heading">
      <h1 id="explore-heading">{t("explore.heading")}</h1>
      <p className="lead">{t("explore.lead")}</p>
      <StateMessage variant="empty" />
    </section>
  );
}
