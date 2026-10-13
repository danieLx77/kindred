import { screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { paths } from './routes'
import { renderApp } from './test/renderApp'

function mainNav() {
  return screen.getByRole('navigation', { name: 'Navegação principal' })
}

describe('rotas', () => {
  it('renderiza cada rota conhecida', () => {
    const { unmount } = renderApp({ route: '/', language: 'pt-BR' })
    expect(
      screen.getByRole('heading', { level: 1, name: 'Bem-vindo à Kindred' }),
    ).toBeInTheDocument()
    unmount()

    const second = renderApp({ route: '/explore', language: 'pt-BR' })
    expect(
      screen.getByRole('heading', { level: 1, name: 'Explorar projetos' }),
    ).toBeInTheDocument()
    second.unmount()

    renderApp({ route: '/projects/42', language: 'pt-BR' })
    expect(
      screen.getByRole('heading', { level: 1, name: 'Detalhes do projeto' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Identificador do projeto: 42')).toBeInTheDocument()
  })

  it('lê o id de /projects/:id e decodifica caracteres especiais', () => {
    renderApp({ route: paths.project('a b/c'), language: 'pt-BR' })

    expect(
      screen.getByText('Identificador do projeto: a b/c'),
    ).toBeInTheDocument()
  })

  it('mostra a página 404 numa rota desconhecida, mantendo o shell', () => {
    renderApp({ route: '/isto/nao/existe', language: 'pt-BR' })

    expect(
      screen.getByRole('heading', { level: 1, name: 'Página não encontrada' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('banner')).toBeInTheDocument()
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })

  it.each(['/projects', '/projects/1/extra', '/explore/algo'])(
    'trata %s como rota desconhecida',
    (route) => {
      renderApp({ route, language: 'pt-BR' })

      expect(
        screen.getByRole('heading', { level: 1, name: 'Página não encontrada' }),
      ).toBeInTheDocument()
    },
  )

  it('permite sair da 404 para o início', async () => {
    const { user } = renderApp({ route: '/nada', language: 'pt-BR' })

    await user.click(
      screen.getByRole('link', { name: 'Voltar para o início' }),
    )

    expect(
      screen.getByRole('heading', { level: 1, name: 'Bem-vindo à Kindred' }),
    ).toBeInTheDocument()
  })
})

describe('navegação', () => {
  it('navega entre Início e Explorar pelo menu e marca a página atual', async () => {
    const { user } = renderApp({ language: 'pt-BR' })
    const nav = within(mainNav())

    expect(nav.getByRole('link', { name: 'Início' })).toHaveAttribute(
      'aria-current',
      'page',
    )

    await user.click(nav.getByRole('link', { name: 'Explorar' }))

    expect(
      screen.getByRole('heading', { level: 1, name: 'Explorar projetos' }),
    ).toBeInTheDocument()
    expect(nav.getByRole('link', { name: 'Explorar' })).toHaveAttribute(
      'aria-current',
      'page',
    )
    expect(nav.getByRole('link', { name: 'Início' })).not.toHaveAttribute(
      'aria-current',
    )

    await user.click(nav.getByRole('link', { name: 'Início' }))

    expect(
      screen.getByRole('heading', { level: 1, name: 'Bem-vindo à Kindred' }),
    ).toBeInTheDocument()
  })

  it('o botão da Home leva a Explorar', async () => {
    const { user } = renderApp({ language: 'pt-BR' })

    await user.click(screen.getByRole('link', { name: 'Explorar projetos' }))

    expect(
      screen.getByRole('heading', { level: 1, name: 'Explorar projetos' }),
    ).toBeInTheDocument()
  })

  it('a página de projeto volta para Explorar', async () => {
    const { user } = renderApp({ route: '/projects/7', language: 'pt-BR' })

    await user.click(screen.getByRole('link', { name: 'Voltar para Explorar' }))

    expect(
      screen.getByRole('heading', { level: 1, name: 'Explorar projetos' }),
    ).toBeInTheDocument()
  })

  it('não marca nenhum item do menu como atual numa rota desconhecida', () => {
    renderApp({ route: '/nada', language: 'pt-BR' })
    const nav = within(mainNav())

    expect(nav.getByRole('link', { name: 'Início' })).not.toHaveAttribute(
      'aria-current',
    )
    expect(nav.getByRole('link', { name: 'Explorar' })).not.toHaveAttribute(
      'aria-current',
    )
  })

  it('atualiza o título do documento a cada rota', async () => {
    const { user } = renderApp({ language: 'pt-BR' })
    expect(document.title).toBe('Início · Kindred')

    await user.click(
      within(mainNav()).getByRole('link', { name: 'Explorar' }),
    )
    expect(document.title).toBe('Explorar · Kindred')
  })

  it('usa o título da página 404 numa rota desconhecida', () => {
    renderApp({ route: '/nada', language: 'pt-BR' })

    expect(document.title).toBe('Página não encontrada · Kindred')
  })
})

describe('paths', () => {
  it('constrói links de projeto com o id codificado', () => {
    expect(paths.project(42)).toBe('/projects/42')
    expect(paths.project('a b/c')).toBe('/projects/a%20b%2Fc')
  })
})
