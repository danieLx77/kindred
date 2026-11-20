import type { Translation } from "./pt-BR";

const en: Translation = {
  app: {
    name: "Kindred",
  },
  a11y: {
    skipToContent: "Skip to main content",
    mainNavigation: "Main navigation",
  },
  nav: {
    home: "Home",
    explore: "Explore",
  },
  language: {
    label: "Language",
    pt: "Portuguese (Brazil)",
    en: "English (United States)",
  },
  footer: {
    copyright: "© {{year}} Kindred",
    dataSource: "Project data source",
    externalContent:
      "Project and organization content comes from external sources and is shown in its original language.",
  },
  states: {
    loading: "Loading…",
    error: "Something went wrong. Please try again.",
    empty: "Nothing to show here yet.",
    retry: "Try again",
  },
  home: {
    title: "Home",
    heading: "Discover social impact projects",
    lead: "Kindred helps you find social initiatives and learn about the work they do.",
    cta: "Explore projects",
    searchLabel: "Search social projects",
    searchSubmit: "Search",
    guideHeading: "From discovery to the official project page",
    guideDescription:
      "Start in Explore or enter a search term. When an official project page is available, follow its link to learn more directly from the initiative.",
  },
  explore: {
    title: "Explore",
    heading: "Explore projects",
    lead: "Browse the catalog or search for social projects.",
    searchLabel: "Search social projects",
    search: "Search",
    clear: "Clear search",
    results: "Project results",
    loading: "Loading projects…",
    noMatches: "No projects match this search.",
    empty: "No projects are available right now.",
    end: "No more results on this page.",
    error: "Projects could not be loaded. Please try again.",
    invalidCursor: "This page link has expired. Start again from the first page.",
    paginationLabel: "Project pages",
    previous: "Previous",
    next: "Next",
    first: "First page",
    page: "Page {{page}}",
    untitledProject: "Project {{id}}",
  },
  project: {
    title: "Project details",
    heading: "Project details",
    loading: "Loading project details…",
    notFound: "Project not found.",
    invalidId: "This project identifier is invalid.",
    error: "Project details could not be loaded. Please try again.",
    theme: "Theme",
    location: "Location",
    organization: "Organization",
    organizationReference: "Reference {{id}}",
    official: "Visit the official project page (external site)",
    activities: "Activities",
    need: "What the project addresses",
    impact: "Long-term impact",
    back: "Back to Explore",
  },
  notFound: {
    title: "Page not found",
    heading: "Page not found",
    message: "The address you opened does not exist or has been moved.",
    backHome: "Back to home",
  },
};

export default en;
