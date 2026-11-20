import { http, HttpResponse } from "msw/http";
import { setupServer } from "msw/node";

// Route and shell tests use the default API states without a running backend.
export const server = setupServer(
  http.get(new URL("/api/v1/projects", window.location.href).href, () =>
    HttpResponse.json({ items: [], pagination: { page: 1, page_size: 10, next_cursor: null } }),
  ),
  http.get(new URL("/api/v1/projects/:id", window.location.href).href, () =>
    HttpResponse.json({ code: "project_not_found" }, { status: 404 }),
  ),
);
