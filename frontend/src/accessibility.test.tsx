import { screen, within } from '@testing-library/react'
import { StrictMode } from 'react'
import { describe, expect, it } from 'vitest'
import App from './App'
import { renderApp, renderWithProviders } from './test/renderApp'

describe('pontos de referência e cabeçalhos', () => {
  it.each(['/', '/explore', '/projects/1', '/pagina-inexistente'])(
    'em %s há um único banner, nav, main, contentinfo e h1',
    (route) => {
      renderApp({ route, language: 'pt-BR' })

      expect(screen.getAllByRole('banner')).toHaveLength(1)
      expect(screen.getAllByRole('navigation')).toHaveLength(1)
      expect(screen.getAllByRole('main')).toHaveLength(1)
      expect(screen.getAllByRole('contentinfo')).toHaveLength(1)
      expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    },
  )

  it('o <nav> e o seletor de idioma ficam dentro do <header>', () => {
    renderApp({ language: 'pt-BR' })
    const header = within(screen.getByRole('banner'))

    expect(header.getByRole('navigation')).toBeInTheDocument()
    expect(header.getByRole('group', { name: 'Idioma' })).toBeInTheDocument()
  })

  it('nenhum elemento usa tabindex positivo', () => {
    renderApp({ language: 'pt-BR' })

    for (const element of document.querySelectorAll('[tabindex]')) {
      expect(Number(element.getAttribute('tabindex'))).toBeLessThanOrEqual(0)
    }
  })
})

describe('navegação por teclado', () => {
  it('percorre os controlos pela ordem visual com Tab', async () => {
    const { user } = renderApp({ language: 'pt-BR' })

    const expectedOrder = [
      screen.getByRole('link', { name: 'Ir para o conteúdo principal' }),
      screen.getByRole('link', { name: 'Kindred' }),
      screen.getByRole('link', { name: 'Início' }),
      screen.getByRole('link', { name: 'Explorar' }),
      screen.getByRole('button', { name: 'Português' }),
      screen.getByRole('button', { name: 'English' }),
      screen.getByRole('link', { name: 'Explorar projetos' }),
    ]

    for (const element of expectedOrder) {
      await user.tab()
      expect(element).toHaveFocus()
    }
  })

  it('Shift+Tab volta atrás na mesma ordem', async () => {
    const { user } = renderApp({ language: 'pt-BR' })
    const english = screen.getByRole('button', { name: 'English' })
    const portuguese = screen.getByRole('button', { name: 'Português' })

    english.focus()
    await user.tab({ shift: true })

    expect(portuguese).toHaveFocus()
  })

  it('o skip link é o primeiro foco e leva o foco ao <main>', async () => {
    const { user } = renderApp({ language: 'pt-BR' })

    await user.tab()
    expect(
      screen.getByRole('link', { name: 'Ir para o conteúdo principal' }),
    ).toHaveFocus()

    await user.keyboard('{Enter}')
    expect(screen.getByRole('main')).toHaveFocus()
  })

  it('Enter num link do menu navega e move o foco para o <main>', async () => {
    const { user } = renderApp({ language: 'pt-BR' })

    await user.tab()
    await user.tab()
    await user.tab()
    await user.tab()
    expect(screen.getByRole('link', { name: 'Explorar' })).toHaveFocus()

    await user.keyboard('{Enter}')

    expect(
      screen.getByRole('heading', { level: 1, name: 'Explorar projetos' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('main')).toHaveFocus()
  })

  it('não rouba o foco no primeiro render (nem em StrictMode)', () => {
    renderWithProviders(
      <StrictMode>
        <App />
      </StrictMode>,
      { language: 'pt-BR' },
    )

    expect(screen.getByRole('main')).not.toHaveFocus()
    expect(document.body).toHaveFocus()
  })

  it('trocar de idioma não move o foco do botão', async () => {
    const { user } = renderApp({ language: 'pt-BR' })
    const english = screen.getByRole('button', { name: 'English' })

    english.focus()
    await user.keyboard('{Enter}')

    expect(
      screen.getByRole('heading', { level: 1, name: 'Welcome to Kindred' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'English' })).toHaveFocus()
  })

  it('Enter e Espaço ativam o seletor de idioma', async () => {
    const { user } = renderApp({ language: 'pt-BR' })

    screen.getByRole('button', { name: 'English' }).focus()
    await user.keyboard('{Enter}')
    expect(
      screen.getByRole('button', { name: 'English' }),
    ).toHaveAttribute('aria-pressed', 'true')

    screen.getByRole('button', { name: 'Português' }).focus()
    await user.keyboard(' ')
    expect(
      screen.getByRole('button', { name: 'Português' }),
    ).toHaveAttribute('aria-pressed', 'true')
    expect(
      screen.getByRole('heading', { level: 1, name: 'Bem-vindo à Kindred' }),
    ).toBeInTheDocument()
  })

  it('a escolha de idioma feita por teclado persiste', async () => {
    const { user } = renderApp({ language: 'pt-BR' })

    screen.getByRole('button', { name: 'English' }).focus()
    await user.keyboard('{Enter}')

    expect(window.localStorage.getItem('kindred.language')).toBe('en')
  })
})
