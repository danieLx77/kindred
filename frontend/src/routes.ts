export const paths = {
  home: "/",
  explore: "/explore",
  projectPattern: "/projects/:id",
  project: (id: string | number) => `/projects/${encodeURIComponent(String(id))}`,
} as const;
