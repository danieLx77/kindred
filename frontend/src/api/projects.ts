export const discoveryPath = "/api/v1/projects";
export const explorePageSize = 9;

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

export interface ProjectDetail extends ProjectCard {
  need?: string | null;
  activities?: string | null;
  long_term_impact?: string | null;
  region?: string | null;
  official_url?: string | null;
}

export interface DiscoveryResponse {
  items: ProjectCard[];
  pagination: { page: number; page_size: number; next_cursor: string | null };
}

export class KindredApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(code: string, status: number) {
    super("Kindred API request failed");
    this.code = code;
    this.status = status;
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

async function fetchKindred(url: URL, signal: AbortSignal): Promise<unknown> {
  const response = await fetch(url, {
    signal,
    redirect: "error",
    headers: { Accept: "application/json" },
  });
  const body: unknown = await response.json().catch(() => {
    if (response.ok) throw new KindredApiError("invalid_response", response.status);
    return null;
  });
  if (!response.ok) {
    const code = isRecord(body) && typeof body.code === "string" ? body.code : "request_failed";
    throw new KindredApiError(code, response.status);
  }
  return body;
}

export async function fetchProjects(query: string, cursor: string | null, signal: AbortSignal) {
  const url = new URL(discoveryPath, window.location.origin);
  url.searchParams.set("page_size", String(explorePageSize));
  if (query) url.searchParams.set("q", query);
  if (cursor !== null) url.searchParams.set("cursor", cursor);

  const body = await fetchKindred(url, signal);
  if (!isDiscoveryResponse(body)) throw new KindredApiError("invalid_response", 200);
  return body;
}

function isProjectDetail(value: unknown): value is ProjectDetail {
  return (
    isRecord(value) &&
    [value.need, value.activities, value.long_term_impact, value.region, value.official_url].every(
      optionalText,
    ) &&
    isCard(value)
  );
}

export async function fetchProject(id: string, signal: AbortSignal): Promise<ProjectDetail> {
  const url = new URL(`${discoveryPath}/${encodeURIComponent(id)}`, window.location.origin);
  const body = await fetchKindred(url, signal);
  if (!isProjectDetail(body) || body.id !== id) {
    throw new KindredApiError("invalid_response", 200);
  }
  return body;
}
