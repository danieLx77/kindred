import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

type StateVariant = "loading" | "error" | "empty";

interface StateMessageProps {
  variant: StateVariant;
  children?: ReactNode;
  onRetry?: () => void;
}

export function StateMessage({ variant, children, onRetry }: StateMessageProps) {
  const { t } = useTranslation();

  return (
    <div
      className={`state-message state-message--${variant}`}
      role={variant === "error" ? "alert" : "status"}
    >
      <p>{children ?? t(`states.${variant}`)}</p>
      {variant === "error" && onRetry ? (
        <button type="button" className="button" onClick={onRetry}>
          {t("states.retry")}
        </button>
      ) : null}
    </div>
  );
}
