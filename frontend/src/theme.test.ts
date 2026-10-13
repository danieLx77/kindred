import { describe, expect, it } from 'vitest'
import css from './index.css?raw'

function readTokens(source: string): Record<string, string> {
  const root = source.match(/:root\s*\{([\s\S]*?)\n\}/)?.[1] ?? ''
  const tokens: Record<string, string> = {}
  for (const [, name, value] of root.matchAll(
    /--color-([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;/g,
  )) {
    tokens[name] = value.toLowerCase()
  }
  return tokens
}

function channels(hex: string): [number, number, number] {
  return [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16)) as [
    number,
    number,
    number,
  ]
}

function luminance(hex: string): number {
  const [r, g, b] = channels(hex).map((value) => {
    const c = value / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contrast(a: string, b: string): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (light + 0.05) / (dark + 0.05)
}

function isGreen(hex: string): boolean {
  const [r, g, b] = channels(hex)
  return g > r && g > b
}

const color = readTokens(css)

describe('tema verde e branco', () => {
  it('declara todos os tokens de cor esperados', () => {
    for (const name of [
      'bg',
      'bg-soft',
      'surface',
      'primary',
      'primary-strong',
      'on-primary',
      'text',
      'muted',
      'focus',
      'danger',
      'danger-surface',
    ]) {
      expect(color[name], `--color-${name}`).toBeDefined()
    }
  })

  it('é um tema claro: fundos quase brancos e texto escuro', () => {
    expect(luminance(color.bg)).toBeGreaterThan(0.9)
    expect(luminance(color['bg-soft'])).toBeGreaterThan(0.9)
    expect(luminance(color.surface)).toBeGreaterThan(0.8)
    expect(luminance(color.text)).toBeLessThan(0.05)
  })

  it('usa verde como cor primária, de destaque e dos cartões', () => {
    expect(isGreen(color.primary)).toBe(true)
    expect(isGreen(color['primary-strong'])).toBe(true)
    expect(isGreen(color.surface)).toBe(true)
  })

  it('declara a fonte do corpo e dos títulos com alternativas do sistema', () => {
    expect(css).toMatch(/--font-body:[^;]*'Figtree Variable'[^;]*system-ui/)
    expect(css).toMatch(/--font-display:[^;]*'Young Serif'[^;]*serif/)
  })

  it('não define modo escuro (a identidade é clara)', () => {
    expect(css).toMatch(/color-scheme:\s*light\s*;/)
    expect(css).not.toMatch(/prefers-color-scheme:\s*dark/)
  })

  describe('contraste de texto (WCAG AA ≥ 4.5:1)', () => {
    const backgrounds = ['bg', 'bg-soft', 'surface']

    it.each(backgrounds)('texto principal sobre %s', (background) => {
      expect(contrast(color.text, color[background])).toBeGreaterThanOrEqual(4.5)
    })

    it.each(backgrounds)('texto secundário sobre %s', (background) => {
      expect(contrast(color.muted, color[background])).toBeGreaterThanOrEqual(4.5)
    })

    it.each(backgrounds)('links e títulos verdes sobre %s', (background) => {
      expect(
        contrast(color['primary-strong'], color[background]),
      ).toBeGreaterThanOrEqual(4.5)
    })

    it('texto branco sobre botões primários (normal e hover)', () => {
      expect(contrast(color['on-primary'], color.primary)).toBeGreaterThanOrEqual(4.5)
      expect(
        contrast(color['on-primary'], color['primary-strong']),
      ).toBeGreaterThanOrEqual(4.5)
    })

    it('texto principal sobre o cartão de erro', () => {
      expect(
        contrast(color.text, color['danger-surface']),
      ).toBeGreaterThanOrEqual(4.5)
    })
  })

  describe('contraste de elementos não textuais (WCAG ≥ 3:1)', () => {
    it.each(['bg', 'surface'])('contorno de foco sobre %s', (background) => {
      expect(contrast(color.focus, color[background])).toBeGreaterThanOrEqual(3)
    })

    it.each(['bg', 'surface'])(
      'indicador e contornos verdes sobre %s',
      (background) => {
        expect(contrast(color.primary, color[background])).toBeGreaterThanOrEqual(3)
      },
    )

    it('contorno do cartão de erro sobre o seu fundo', () => {
      expect(
        contrast(color.danger, color['danger-surface']),
      ).toBeGreaterThanOrEqual(3)
    })
  })
})
