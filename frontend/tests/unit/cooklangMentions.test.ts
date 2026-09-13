import { describe, expect, it } from 'vitest'
import { findOrphanMentions, parseIngredientMentions, toMentionToken } from '../../src/utils/cooklangMentions'

describe('parseIngredientMentions', () => {
  it('parses a single-word mention without quantity', () => {
    const mentions = parseIngredientMentions('Peler la @pomme de terre.')
    expect(mentions).toHaveLength(1)
    expect(mentions[0].displayName).toBe('pomme')
  })

  it('parses a multi-word mention (underscore-joined) with a quantity', () => {
    const mentions = parseIngredientMentions('Ajouter @huile_olive{2%cs} dans la poêle.')
    expect(mentions).toHaveLength(1)
    expect(mentions[0].name).toBe('huile_olive')
    expect(mentions[0].displayName).toBe('huile olive')
  })

  it('parses several mentions in the same text', () => {
    const mentions = parseIngredientMentions('Mélanger @sel et @poivre puis servir.')
    expect(mentions.map((m) => m.displayName)).toEqual(['sel', 'poivre'])
  })

  it('returns no mentions when there is no "@"', () => {
    expect(parseIngredientMentions('Faire cuire 10 minutes.')).toEqual([])
  })

  it('exposes start/end offsets covering the full mention including {meta}', () => {
    const text = 'Ajouter @sel{1%pincée} maintenant.'
    const [mention] = parseIngredientMentions(text)
    expect(text.slice(mention.start, mention.end)).toBe('@sel{1%pincée}')
  })
})

describe('findOrphanMentions', () => {
  it('is empty when every mention matches a known ingredient (case-insensitive)', () => {
    const orphans = findOrphanMentions('Ajouter le @Sel et le @poivre puis mélanger.', ['sel', 'Poivre'])
    expect(orphans).toEqual([])
  })

  it('reports a mention that has no matching ingredient in the list', () => {
    const orphans = findOrphanMentions('Ajouter le @poireau puis mélanger.', ['sel', 'poivre'])
    expect(orphans.map((m) => m.displayName)).toEqual(['poireau'])
  })

  it('matches multi-word ingredients written with an underscore', () => {
    const orphans = findOrphanMentions("Verser l'@huile_olive puis mélanger.", ['huile olive'])
    expect(orphans).toEqual([])
  })
})

describe('toMentionToken', () => {
  it('joins a multi-word ingredient name with underscores', () => {
    expect(toMentionToken('huile olive')).toBe('@huile_olive')
  })

  it('leaves a single-word name untouched', () => {
    expect(toMentionToken('sel')).toBe('@sel')
  })
})
