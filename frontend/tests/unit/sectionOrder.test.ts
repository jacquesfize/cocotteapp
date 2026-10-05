import { describe, expect, it } from 'vitest'
import { orderRowsBySection, sectionNamesOf } from '../../src/utils/ingredientSections'

const row = (group_name: string, order: number) => ({ group_name, order })

describe('sectionNamesOf', () => {
  it('lists the sections in order of appearance', () => {
    expect(sectionNamesOf([row('Garniture', 1), row('Pâte', 2), row('Garniture', 3)])).toEqual(['Garniture', 'Pâte'])
  })

  it('has a single unnamed section when there is no row', () => {
    expect(sectionNamesOf([])).toEqual([''])
  })
})

describe('orderRowsBySection', () => {
  it('groups rows by section, keeps their relative order and renumbers them', () => {
    const rows = [row('Pâte', 1), row('', 2), row('Pâte', 3), row('Garniture', 4)]
    expect(orderRowsBySection(rows).map((item) => [item.group_name, item.order])).toEqual([
      ['Pâte', 1],
      ['Pâte', 2],
      ['', 3],
      ['Garniture', 4],
    ])
  })

  it('follows an explicit section order, and appends sections it does not list', () => {
    const rows = [row('A', 1), row('B', 2), row('C', 3)]
    expect(orderRowsBySection(rows, ['', 'C', 'A']).map((item) => item.group_name)).toEqual(['C', 'A', 'B'])
  })
})
