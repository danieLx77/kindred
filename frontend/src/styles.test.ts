/// <reference types="node" />
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import indexHtml from "../index.html?raw";

const css = readFileSync("src/index.css", "utf8");

describe("contrato de estilos (acessibilidade e responsividade)", () => {
  it("define um indicador de foco visível para elementos interativos", () => {
    expect(css).toMatch(/:focus-visible\s*\{[^}]*outline:\s*3px solid/);
  });

  it("nunca remove o contorno de foco dos controlos", () => {
    const cssWithoutComments = css.replace(/\/\*[\s\S]*?\*\//g, "");
    const rulesWithoutOutline = [
      ...cssWithoutComments.matchAll(/([^{}]+)\{[^}]*outline:\s*none[^}]*\}/g),
    ].map((match) => match[1].trim());

    expect(rulesWithoutOutline).toEqual([".app-main:focus"]);
  });

  it("declara o viewport para mobile e o idioma padrão no HTML", () => {
    expect(indexHtml).toMatch(/<meta name="viewport"[^>]*width=device-width/);
    expect(indexHtml).toMatch(/<html lang="pt-BR">/);
  });

  it("prepara o layout para ecrãs estreitos (quebra de linha e textos longos)", () => {
    expect(css).toMatch(/flex-wrap:\s*wrap/);
    expect(css).toMatch(/overflow-wrap:\s*anywhere/);
  });
});
