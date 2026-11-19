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
    pt: "Português",
    en: "English",
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
    lead: "This is where you will find projects to support.",
  },
  project: {
    title: "Project details",
    heading: "Project details",
    identifier: "Project identifier: {{id}}",
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
