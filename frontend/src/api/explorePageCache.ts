import { explorePageSize, type DiscoveryResponse } from "./projects";

const PAGE_TTL_MS = 60_000;
const PAGE_LIMIT = 12;

function pageKey(query: string, cursor: string | null) {
  return JSON.stringify([explorePageSize, query, cursor]);
}

export class ExplorePageCache {
  private readonly pages = new Map<string, { data: DiscoveryResponse; expiresAt: number }>();

  read(query: string, cursor: string | null) {
    const entry = this.pages.get(pageKey(query, cursor));
    return entry && entry.expiresAt > Date.now() ? entry.data : undefined;
  }

  write(query: string, cursor: string | null, data: DiscoveryResponse) {
    const key = pageKey(query, cursor);
    this.pages.delete(key);
    this.pages.set(key, { data, expiresAt: Date.now() + PAGE_TTL_MS });

    if (this.pages.size > PAGE_LIMIT) {
      const oldest = this.pages.keys().next().value;
      if (oldest !== undefined) this.pages.delete(oldest);
    }
  }

  clear() {
    this.pages.clear();
  }
}
