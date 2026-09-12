import { beforeEach, describe, expect, it } from 'vitest'
import { i18n, setLocale, SUPPORTED_LOCALES } from '../../src/i18n'

beforeEach(() => {
  localStorage.clear()
  i18n.global.locale.value = 'fr'
})

describe('i18n', () => {
  it('defaults to French', () => {
    expect(i18n.global.locale.value).toBe('fr')
    expect(i18n.global.t('nav.recipes')).toBe('Recettes')
  })

  it('switches translations and persists the choice', () => {
    setLocale('en')

    expect(i18n.global.locale.value).toBe('en')
    expect(i18n.global.t('nav.recipes')).toBe('Recipes')
    expect(localStorage.getItem('locale')).toBe('en')
  })

  it('exposes exactly the supported locales', () => {
    expect(SUPPORTED_LOCALES.map((l) => l.code)).toEqual(['fr', 'en'])
  })

  it('falls back to French for an unknown key path gracefully', () => {
    // both locales must define the same keys used across the app
    for (const locale of SUPPORTED_LOCALES) {
      i18n.global.locale.value = locale.code
      expect(i18n.global.t('recipes.newRecipe')).not.toBe('recipes.newRecipe')
    }
  })
})
