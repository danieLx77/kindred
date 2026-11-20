import { describe, expect, it, vi } from "vitest";
import { ExplorePageCache } from "./explorePageCache";

const page = {
  items: [{ id: "1" }],
  pagination: { page: 1, page_size: 9, next_cursor: null },
};

describe("cache da Explore", () => {
  it("reutiliza a resposta apenas para o mesmo texto e cursor", () => {
    const cache = new ExplorePageCache();

    expect(cache.read("água", null)).toBeUndefined();
    cache.write("água", null, page);
    expect(cache.read("água", null)).toBe(page);
    expect(cache.read("água", "next")).toBeUndefined();
    expect(cache.read("escola", null)).toBeUndefined();
    expect(cache.read("", null)).toBeUndefined();
  });

  it("expira após 60 segundos a partir da conclusão da requisição", () => {
    const clock = vi.spyOn(Date, "now").mockReturnValue(1000);
    const cache = new ExplorePageCache();
    cache.write("", null, page);

    clock.mockReturnValue(60_999);
    expect(cache.read("", null)).toBe(page);
    clock.mockReturnValue(61_000);
    expect(cache.read("", null)).toBeUndefined();
  });

  it("limita a memória a 12 respostas e descarta a mais antiga", () => {
    const cache = new ExplorePageCache();
    for (let index = 0; index < 13; index++) {
      cache.write("", String(index), page);
    }

    expect(cache.read("", "0")).toBeUndefined();
    for (let index = 1; index < 13; index++) {
      expect(cache.read("", String(index))).toBe(page);
    }
    cache.clear();
    expect(cache.read("", "12")).toBeUndefined();
  });
});
