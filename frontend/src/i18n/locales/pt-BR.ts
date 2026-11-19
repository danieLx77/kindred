const ptBR = {
  app: {
    name: "Kindred",
  },
  a11y: {
    skipToContent: "Ir para o conteúdo principal",
    mainNavigation: "Navegação principal",
  },
  nav: {
    home: "Início",
    explore: "Explorar",
  },
  language: {
    label: "Idioma",
    pt: "Português",
    en: "English",
  },
  footer: {
    copyright: "© {{year}} Kindred",
    dataSource: "Fonte dos dados de projetos",
    externalContent:
      "O conteúdo de projetos e organizações vem de fontes externas e é exibido no idioma original.",
  },
  states: {
    loading: "Carregando…",
    error: "Algo deu errado. Tente novamente.",
    empty: "Nada para mostrar por aqui ainda.",
    retry: "Tentar novamente",
  },
  home: {
    title: "Início",
    heading: "Descubra projetos de impacto social",
    lead: "O Kindred ajuda você a encontrar iniciativas sociais e conhecer o trabalho que elas realizam.",
    cta: "Explorar projetos",
    searchLabel: "Pesquisar projetos sociais",
    searchSubmit: "Pesquisar",
    guideHeading: "Da descoberta à página oficial do projeto",
    guideDescription:
      "Comece pela área Explorar ou digite um termo de busca. Quando houver uma página oficial do projeto, siga o link para saber mais diretamente com a iniciativa.",
  },
  explore: {
    title: "Explorar",
    heading: "Explorar projetos",
    lead: "Aqui você vai encontrar projetos para apoiar.",
  },
  project: {
    title: "Detalhes do projeto",
    heading: "Detalhes do projeto",
    identifier: "Identificador do projeto: {{id}}",
    back: "Voltar para Explorar",
  },
  notFound: {
    title: "Página não encontrada",
    heading: "Página não encontrada",
    message: "O endereço que você abriu não existe ou foi movido.",
    backHome: "Voltar para o início",
  },
};

export type Translation = typeof ptBR;

export default ptBR;
