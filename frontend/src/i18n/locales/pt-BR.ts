const ptBR = {
  app: {
    name: 'Kindred',
  },
  a11y: {
    skipToContent: 'Ir para o conteúdo principal',
    mainNavigation: 'Navegação principal',
  },
  nav: {
    home: 'Início',
    explore: 'Explorar',
  },
  language: {
    label: 'Idioma',
    pt: 'Português',
    en: 'English',
  },
  footer: {
    copyright: '© {{year}} Kindred',
    externalContent:
      'O conteúdo de projetos e organizações vem de fontes externas e é exibido no idioma original.',
  },
  states: {
    loading: 'Carregando…',
    error: 'Algo deu errado. Tente novamente.',
    empty: 'Nada para mostrar por aqui ainda.',
    retry: 'Tentar novamente',
  },
  home: {
    title: 'Início',
    heading: 'Bem-vindo à Kindred',
    lead: 'Descubra projetos de impacto social e apoie as causas que importam para você.',
    cta: 'Explorar projetos',
  },
  explore: {
    title: 'Explorar',
    heading: 'Explorar projetos',
    lead: 'Aqui você vai encontrar projetos para apoiar.',
  },
  project: {
    title: 'Detalhes do projeto',
    heading: 'Detalhes do projeto',
    identifier: 'Identificador do projeto: {{id}}',
    back: 'Voltar para Explorar',
  },
  notFound: {
    title: 'Página não encontrada',
    heading: 'Página não encontrada',
    message: 'O endereço que você abriu não existe ou foi movido.',
    backHome: 'Voltar para o início',
  },
}

export type Translation = typeof ptBR

export default ptBR
