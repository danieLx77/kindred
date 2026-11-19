import { http, HttpResponse } from "msw/http";
import { expect, test } from "vitest";
import { server } from "./server";

test("simula a resposta da rota raiz da Kindred API", async () => {
  const url = new URL("/", window.location.href).href;
  server.use(http.get(url, () => HttpResponse.json({ status: "ok" })));

  const response = await fetch(url);

  expect(response.status).toBe(200);
  expect(await response.json()).toEqual({ status: "ok" });
});
