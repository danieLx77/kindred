import { http, HttpResponse } from "msw";
import { expect, test } from "vitest";
import { server } from "./server";

test("simula a resposta da rota raiz da Kindred API", async () => {
  server.use(http.get("http://kindred.test/", () => HttpResponse.json({ status: "ok" })));

  const response = await fetch("http://kindred.test/");

  expect(response.status).toBe(200);
  expect(await response.json()).toEqual({ status: "ok" });
});
