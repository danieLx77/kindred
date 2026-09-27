import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import App from "./App";

test("mostra a tela inicial e atualiza o contador ao clicar", async () => {
  const user = userEvent.setup();
  render(<App />);

  expect(screen.getByRole("heading", { name: "Get started" })).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Count is 0" }));

  expect(screen.getByRole("button", { name: "Count is 10" })).toBeInTheDocument();
});
