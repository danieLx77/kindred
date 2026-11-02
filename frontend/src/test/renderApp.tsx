import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { i18n as I18nInstance } from "i18next";
import type { ReactElement } from "react";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import { createI18n, type Language } from "../i18n";

interface RenderOptions {
  route?: string;
  language?: Language;
  i18n?: I18nInstance;
}

export function renderWithProviders(
  ui: ReactElement,
  { route = "/", language, i18n }: RenderOptions = {},
) {
  const instance = i18n ?? createI18n(language);
  const user = userEvent.setup();

  const utils = render(
    <I18nextProvider i18n={instance}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </I18nextProvider>,
  );

  return { user, i18n: instance, ...utils };
}

export function renderApp(options?: RenderOptions) {
  return renderWithProviders(<App />, options);
}
