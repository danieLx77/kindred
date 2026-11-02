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
    heading: "Welcome to Kindred",
    lead: "Discover social impact projects and support the causes that matter to you.",
    cta: "Explore projects",
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
