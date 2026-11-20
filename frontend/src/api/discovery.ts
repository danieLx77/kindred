export const discoveryPath = "/api/v1/projects";

interface OrganizationCard {
  id: string;
  name?: string | null;
}

export interface ProjectCard {
  id: string;
  title?: string | null;
  summary?: string | null;
  image_url?: string | null;
  theme?: string | null;
  country?: string | null;
  organization?: OrganizationCard | null;
}

interface DiscoveryResponse {
  items: ProjectCard[];
  pagination: { page: number; page_size: number; next_cursor: string | null };
}

export class DiscoveryError extends Error {
  readonly code: string;

  constructor(code: string) {
    super("Kindred discovery request failed");
    this.code = code;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function optionalText(value: unknown): boolean {
  return value == null || typeof value === "string";
}

function isCard(value: unknown): value is ProjectCard {
  if (!isRecord(value) || typeof value.id !== "string" || !value.id.trim()) return false;
  const { organization } = value;
  return (
    [value.title, value.summary, value.image_url, value.theme, value.country].every(optionalText) &&
    (organization == null ||
      (isRecord(organization) &&
        typeof organization.id === "string" &&
        optionalText(organization.name)))
  );
}

function isDiscoveryResponse(value: unknown): value is DiscoveryResponse {
  if (!isRecord(value) || !Array.isArray(value.items) || !value.items.every(isCard)) return false;
  const { pagination } = value;
  return (
    isRecord(pagination) &&
    typeof pagination.page === "number" &&
    Number.isSafeInteger(pagination.page) &&
    pagination.page > 0 &&
    typeof pagination.page_size === "number" &&
    Number.isInteger(pagination.page_size) &&
    pagination.page_size >= 1 &&
    pagination.page_size <= 10 &&
    (pagination.next_cursor === null ||
      (typeof pagination.next_cursor === "string" && pagination.next_cursor.length > 0))
  );
}

export async function fetchProjects(query: string, cursor: string | null, signal: AbortSignal) {
  const url = new URL(discoveryPath, window.location.origin);
  if (query) url.searchParams.set("q", query);
  if (cursor !== null) url.searchParams.set("cursor", cursor);

  const response = await fetch(url, {
    signal,
    redirect: "error",
    headers: { Accept: "application/json" },
  });
  const body: unknown = await response.json();
  if (!response.ok) {
    const code = isRecord(body) && typeof body.code === "string" ? body.code : "request_failed";
    throw new DiscoveryError(code);
  }
  if (!isDiscoveryResponse(body)) throw new DiscoveryError("invalid_response");
  return body;
}
