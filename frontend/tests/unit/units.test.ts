import { afterEach, describe, expect, it } from 'vitest'
import { i18n } from '../../src/i18n'
import en from '../../src/i18n/locales/en.json'
import fr from '../../src/i18n/locales/fr.json'
import { formatUnit } from '../../src/utils/format'

const ALL_UNITS = ['g', 'kg', 'ml', 'l', 'piece', 'tbsp', 'tsp', 'pinch']

afterEach(() => {
  i18n.global.locale.value = 'fr'
})

describe('units i18n keys', () => {
  it('cover every unit in both locales', () => {
    for (const unit of ALL_UNITS) {
      expect((fr as any).units[unit]).toBeTruthy()
      expect((en as any).units[unit]).toBeTruthy()
    }
    expect(Object.keys((fr as any).units).sort()).toEqual([...ALL_UNITS].sort())
    expect(Object.keys((en as any).units).sort()).toEqual([...ALL_UNITS].sort())
  })
})

describe('formatUnit', () => {
  it('translates units in French', () => {
    i18n.global.locale.value = 'fr'
    expect(formatUnit('pinch')).toBe('pincée')
    expect(formatUnit('tbsp')).toBe('c. à soupe')
    expect(formatUnit('tsp')).toBe('c. à café')
    expect(formatUnit('piece')).toBe('pièce')
  })

  it('translates units in English', () => {
    i18n.global.locale.value = 'en'
    expect(formatUnit('pinch')).toBe('pinch')
    expect(formatUnit('piece')).toBe('piece')
  })

  it('agrees with the displayed quantity in French (plural from 2)', () => {
    i18n.global.locale.value = 'fr'
    expect(formatUnit('piece', 1)).toBe('pièce')
    expect(formatUnit('piece', '2.00')).toBe('pièces')
    expect(formatUnit('piece', '1.50')).toBe('pièce') // affiché "1.5", encore singulier (< 2)
    expect(formatUnit('pinch', 1)).toBe('pincée')
    expect(formatUnit('pinch', 3)).toBe('pincées')
    expect(formatUnit('tbsp', 3)).toBe('c. à soupe')
    expect(formatUnit('g', 200)).toBe('g')
  })

  it('agrees with the displayed quantity in English (plural unless 1)', () => {
    i18n.global.locale.value = 'en'
    expect(formatUnit('piece', 1)).toBe('piece')
    expect(formatUnit('piece', 2)).toBe('pieces')
    expect(formatUnit('pinch', 2)).toBe('pinches')
    expect(formatUnit('tbsp', 2)).toBe('tbsp')
  })

  it('falls back to the raw value when unknown, empty when missing', () => {
    expect(formatUnit('bunch')).toBe('bunch')
    expect(formatUnit(null)).toBe('')
  })
})
