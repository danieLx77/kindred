import { http, HttpResponse } from "msw/http";
import { setupServer } from "msw/node";

// Route and shell tests render Explore without needing a running backend.
export const server = setupServer(
  http.get(new URL("/api/v1/projects", window.location.href).href, () =>
    HttpResponse.json({ items: [], pagination: { page: 1, page_size: 10, next_cursor: null } }),
  ),
);
